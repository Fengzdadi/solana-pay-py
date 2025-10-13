# scripts/qr_transfer.py


import os, sys
parentddir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.append(parentddir)

from decimal import Decimal
import qrcode
from solanapay.urls import TransferRequest, encode_url

RECIPIENT = "DL7GeJGi1BvX2QNSQ3Ceav25thDgo4EAYQX2x1ZVxJVr"   # 可用你自己钱包
AMOUNT = Decimal("0.001")
LABEL = "Demo Merchant"
MESSAGE = "Thanks from QR"
MEMO = "INV#QR-DEMO-001"

req = TransferRequest(
    recipient=RECIPIENT,
    amount=AMOUNT,
    label=LABEL,
    message=MESSAGE,
    memo=MEMO
)
url = encode_url(req)
print("Solana Pay URL:", url)
url = url.replace("solana://", "solana:")
print("Solana Pay URL:", url)

img = qrcode.make(url)
img.save("qr_transfer.png")
print("已生成二维码: qr_transfer.png（Phantom Devnet 扫码测试）")