function showPaymentCode(walletId, id) {
    amount=document.getElementById("payment-amount-"+id).value;
    paymentUrl = "algorand://" + walletId + "?amount=" + amount*1000*1000;
    new QRCode(document.getElementById("payment-code-"+id), paymentUrl);
    console.log(paymentUrl)
}