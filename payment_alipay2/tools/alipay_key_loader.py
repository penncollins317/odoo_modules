import textwrap
from cryptography.hazmat.primitives import serialization


class AlipayKeyLoader:
    """
    支付宝密钥加载工具
    功能：
    - 自动识别 PKCS1 / PKCS8
    - 自动补 PEM 头
    - 自动格式化 Base64
    - 统一输出 PKCS1 PEM（兼容 rsa.PrivateKey._load_pkcs1_pem）
    """

    @staticmethod
    def _normalize_key(key_str: str, is_public: bool) -> bytes:
        """
        规范化密钥：
        - 补 BEGIN/END
        - 64位换行
        """
        key_str = key_str.strip()

        if "BEGIN" not in key_str:
            key_str = "\n".join(textwrap.wrap(key_str, 64))

            if is_public:
                key_str = f"-----BEGIN PUBLIC KEY-----\n{key_str}\n-----END PUBLIC KEY-----"
            else:
                key_str = f"-----BEGIN PRIVATE KEY-----\n{key_str}\n-----END PRIVATE KEY-----"

        return key_str.encode()

    # =========================
    # 私钥
    # =========================
    @staticmethod
    def load_private_key(path: str) -> str:
        """
        加载私钥 → 返回 PKCS1 PEM 字符串
        """
        with open(path, "r") as f:
            key_str = f.read()

        key_bytes = AlipayKeyLoader._normalize_key(key_str, is_public=False)

        private_key = serialization.load_pem_private_key(
            key_bytes,
            password=None
        )

        # 🔥 转 PKCS1（关键）
        pkcs1_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        return pkcs1_pem.decode()

    # =========================
    # 公钥
    # =========================
    @staticmethod
    def load_public_key(path: str) -> str:
        """
        加载支付宝公钥 → 返回 PKCS1 PEM 字符串
        """
        with open(path, "r") as f:
            key_str = f.read()

        key_bytes = AlipayKeyLoader._normalize_key(key_str, is_public=True)

        public_key = serialization.load_pem_public_key(key_bytes)

        # 🔥 转 PKCS1（RSA PUBLIC KEY）
        pkcs1_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.PKCS1
        )

        return pkcs1_pem.decode()

    # =========================
    # 可选：直接加载字符串（非文件）
    # =========================
    @staticmethod
    def load_private_key_from_str(key_str: str) -> str:
        key_bytes = AlipayKeyLoader._normalize_key(key_str, is_public=False)

        private_key = serialization.load_pem_private_key(
            key_bytes,
            password=None
        )

        pkcs1_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        return pkcs1_pem.decode()

    @staticmethod
    def load_public_key_from_str(key_str: str) -> str:
        key_bytes = AlipayKeyLoader._normalize_key(key_str, is_public=True)

        public_key = serialization.load_pem_public_key(key_bytes)

        pkcs1_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.PKCS1
        )

        return pkcs1_pem.decode()
