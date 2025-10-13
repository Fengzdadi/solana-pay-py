import pytest
import asyncio
from decimal import Decimal
from solana.rpc.async_api import AsyncClient
from solanapay.tx_builders.transfer import build_transfer_tx
from solanapay.urls import TransferRequest
from solanapay.validation.confirm import wait_and_verify

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_sol_payment_devnet():
    payer = "DL7GeJGi1BvX2QNSQ3Ceav25thDgo4EAYQX2x1ZVxJVr"
    recipient = "DL7GeJGi1BvX2QNSQ3Ceav25thDgo4EAYQX2x1ZVxJVr"
    amount = Decimal("0.001")

    async with AsyncClient("https://api.devnet.solana.com") as rpc:
        # 1. 构造交易
        tx_b64 = await build_transfer_tx(
            rpc,
            payer=payer,
            recipient=recipient,
            amount=amount,
            memo="E2E TEST",
        )
        assert len(tx_b64) > 100

        # 2. 模拟用户用钱包签名并上链
        print("\n👉 打开 Phantom, 手动发送 0.001 SOL 到收款地址:", recipient)
        print("然后把交易 signature 粘贴在这里：")
        signature = input("signature: ").strip()

        # 3. 验证交易
        expected = TransferRequest(recipient=recipient, amount=amount, memo="E2E TEST")
        result = await wait_and_verify(
            rpc_client=rpc,
            signature=signature,
            expected=expected,
            timeout=60,
            commitment="confirmed",
        )

        assert result.is_valid, f"验证失败: {result.errors}"
        print("✅ 交易验证通过:", result)