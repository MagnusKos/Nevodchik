"""Meshtastic protocol decoder."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from Crypto.Cipher import AES
from Crypto.Util import Counter

from generated.meshtastic import mesh_pb2, mqtt_pb2, portnums_pb2

from .decoder import Decoder
from .message_processor import MessageInfo, MessageText

logger = logging.getLogger(__name__)


class DecoderMeshtastic(Decoder):
    """Decode meshtastic MQTT messages."""

    # Default meshtastic key, that is shortened to AQ==
    default_psk = bytes(
        [
            0xD4,
            0xF1,
            0xBB,
            0x3A,
            0x20,
            0x29,
            0x07,
            0x59,
            0xF0,
            0xBC,
            0xFF,
            0xAB,
            0xCF,
            0x4E,
            0x69,
            0x01,
        ]
    )

    def can_decode(self, topic: str, payload: bytes) -> bool:
        return "msh/" in topic  # This needs to be more specific

    def decode(self, topic: str, payload: bytes) -> MessageText | MessageInfo | None:
        try:
            envelope = mqtt_pb2.ServiceEnvelope()
            envelope.ParseFromString(payload)
            mesh_packet = envelope.packet

            data = self._decrypt_mesh_packet(mesh_packet)
            if data is None:
                return None

            if data.portnum != portnums_pb2.TEXT_MESSAGE_APP:
                logger.debug(f"Not a text message: portnum={data.portnum}")
                return None

            parsed_topic = self._parse_mqtt_topic(topic)
            if not parsed_topic:
                return None

            text = data.payload.decode("utf-8", errors="ignore").strip()

            sent_by_int = getattr(mesh_packet, "from", None) or getattr(
                mesh_packet, "from_", 0
            )
            heard_by_int = parsed_topic["device_id"]

            sent_by = f"{sent_by_int:X}"
            heard_by = f"{heard_by_int:X}"

            rx_time = datetime.fromtimestamp(
                mesh_packet.rx_time, tz=timezone.utc
            ).strftime("%H:%M:%S")

            hops_travelled = mesh_packet.hop_start - mesh_packet.hop_limit

            return MessageText(
                proto="Meshtastic",
                sent_by=sent_by,
                heard_by=heard_by,
                ch_name=parsed_topic["channel"],
                rx_rssi=mesh_packet.rx_rssi,
                rx_time=rx_time,
                hops=hops_travelled,
                text=text,
            )

        except Exception as e:
            logger.error(f"Failed to decode message: {e}")
            return None

    @staticmethod
    def _expand_psk(psk_bytes: bytes) -> bytes:
        """
        Expand a short PSK form to 16-byte form, matching firmware behavior.

        From Channels.cpp getKey():
        - If len == 0: encryption disabled
        - If len == 1: the byte is an index into predefined PSKs
          - 0 means encryption disabled
          - 1 means use DEFAULT_PSK as-is
          - N >= 2 means use DEFAULT_PSK with last byte bumped by (N-1)
        - Otherwise: use as-is (pad to 16 or 32 if needed)
        """
        if not psk_bytes or len(psk_bytes) == 0:
            return b""

        if len(psk_bytes) == 1:
            psk_index = psk_bytes[0]
            if psk_index == 0:
                return b""
            if psk_index == 1:
                return DecoderMeshtastic.default_psk
            # For psk_index >= 2, use DEFAULT_PSK with last byte bumped
            expanded = bytearray(DecoderMeshtastic.default_psk)
            expanded[-1] = (expanded[-1] + psk_index - 1) & 0xFF
            return bytes(expanded)

        if len(psk_bytes) < 16:
            return psk_bytes + b"\x00" * (16 - len(psk_bytes))

        if len(psk_bytes) < 32:
            return psk_bytes + b"\x00" * (32 - len(psk_bytes))

        return psk_bytes

    @staticmethod
    def _xor_hash(data: bytes) -> int:
        """Compute XOR hash of bytes (0-255)."""
        result = 0
        for byte in data:
            result ^= byte
        return result & 0xFF

    @staticmethod
    def _generate_channel_hash(channel_name: str, psk: bytes) -> int:
        """
        Generate channel hash from name and PSK, matching firmware.
        Hash = XOR(channel_name_bytes) XOR(psk_bytes)
        """
        if isinstance(channel_name, str):
            channel_name = channel_name.encode("utf-8")
        hash_val = DecoderMeshtastic._xor_hash(channel_name)
        expanded_psk = DecoderMeshtastic._expand_psk(psk)
        hash_val ^= DecoderMeshtastic._xor_hash(expanded_psk)
        return hash_val & 0xFF

    @staticmethod
    def _init_nonce(from_node: int, packet_id: int, extra_nonce: int = 0) -> bytes:
        """
        Initialize nonce for AES-CTR decryption.
        Matches CryptoEngine::initNonce from firmware:
        - memset(nonce, 0, 16)
        - memcpy(nonce+0, &packetId, 8)      // little-endian u64
        - memcpy(nonce+8, &fromNode, 4)      // little-endian u32
        - if (extraNonce) memcpy(nonce+12, &extraNonce, 4)
        """
        nonce = bytearray(16)
        nonce[0:8] = packet_id.to_bytes(8, "little", signed=False)
        nonce[8:12] = from_node.to_bytes(4, "little", signed=False)
        if extra_nonce:
            nonce[12:16] = extra_nonce.to_bytes(4, "little", signed=False)
        return bytes(nonce)

    @staticmethod
    def _decrypt_aes_ctr(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
        """
        AES-CTR decryption matching Meshtastic firmware.
        Nonce is treated as the 128-bit initial counter value.
        """
        ctr = Counter.new(128, initial_value=int.from_bytes(nonce, byteorder="big"))
        cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
        return cipher.decrypt(ciphertext)

    @staticmethod
    def _decrypt_mesh_packet(
        mesh_packet: mesh_pb2.MeshPacket,
        key: Optional[bytes] = None,
        extra_nonce: int = 0,
    ) -> mesh_pb2.Data | None:
        """
        Decrypt a MeshPacket if it has encrypted payload.

        Args:
            mesh_packet: The MeshPacket to decrypt
            key: Encryption key to use. If None, uses DEFAULT_PSK
            extra_nonce: Extra nonce bytes (usually 0 for default channel)

        Returns:
            Decrypted Data protobuf, or None if already decoded or decrypt fails
        """
        # If already decoded, return it
        if mesh_packet.HasField("decoded"):
            return mesh_packet.decoded

        # If not encrypted, nothing to do
        if not mesh_packet.encrypted:
            return None

        # Use default key if not provided
        if key is None:
            key = DecoderMeshtastic.default_psk

        # Get the sender node ID
        from_node = getattr(mesh_packet, "from", None)
        if from_node is None:
            from_node = getattr(mesh_packet, "from_", 0)

        packet_id = mesh_packet.id

        # Build nonce
        nonce = DecoderMeshtastic._init_nonce(
            from_node, packet_id, extra_nonce=extra_nonce
        )

        logger.debug(f"Decrypting packet ID {mesh_packet.id} from node {from_node:08x}")
        logger.debug(f"  Nonce: {nonce.hex()}")
        logger.debug(f"  Key: {key.hex()}")
        logger.debug(f"  Ciphertext length: {len(mesh_packet.encrypted)} bytes")

        # Decrypt
        try:
            plaintext = DecoderMeshtastic._decrypt_aes_ctr(
                key, nonce, mesh_packet.encrypted
            )
            logger.info(f"Plaintext: {plaintext}")
        except Exception as e:
            logger.error(f"AES-CTR decryption failed: {e}")
            return None

        # Parse as Data protobuf
        data = mesh_pb2.Data()
        try:
            data.ParseFromString(plaintext)
            logger.info(
                f"Successfully decrypted packet {mesh_packet.id}, portnum={data.portnum}"
            )
        except Exception as e:
            logger.error(f"Failed to parse Data protobuf: {e}")
            return None
        return data

    @staticmethod
    def _parse_mqtt_topic(topic: str) -> Dict[str, Any] | None:
        """
        Parse Meshtastic MQTT topic.
        Format: msh/<country_code>/<city_code>/2/e/<channel_name>/<device_id>
        """
        parts = topic.split("/")
        if len(parts) < 7 or parts[0] != "msh":
            return None
        try:
            device_id_str = parts[6]
            # Handle short form with '!' prefix
            if device_id_str.startswith("!"):
                device_id_str = device_id_str[1:]
            return {
                "region": parts[1],
                "city_code": parts[2],
                "packet_type": int(parts[3]),
                "encrypted": parts[4] == "e",
                "channel": parts[5],
                "device_id": int(device_id_str, 16),
            }
        except (ValueError, IndexError) as e:
            logger.error(f"Failed to parse topic '{topic}': {e}")
            return None
