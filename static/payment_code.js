// Example POST method implementation:
async function postData(url = '', data = {}) {
  // Default options are marked with *
  const response = await fetch(url, {
    method: 'GET', // *GET, POST, PUT, DELETE, etc.
    mode: 'cors', // no-cors, *cors, same-origin
    cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
    credentials: 'same-origin', // include, *same-origin, omit
    headers: {
      'Content-Type': 'application/json'
      // 'Content-Type': 'application/x-www-form-urlencoded',
    },
    redirect: 'follow', // manual, *follow, error
    referrerPolicy: 'no-referrer', // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-ur// body data type must match "Content-Type" header
  });
  return response; // parses JSON response into native JavaScript objects
}


function showPaymentCodeCollateral(walletId, id) {
    amount=document.getElementById("payment-amount-"+id).value*1000*1000;
    sourceId = document.getElementById("inputWallet").value;
    postData('sendToEscrow?destinationId=' + walletId + '&sourceId=' + sourceId + '&amount=' + amount)
      .then((response) => response.text()).then((data) => {
        document.getElementById("payment-code-"+id).innerHTML = data; // JSON data parsed by `data.json()` call
      });
}


function showPaymentCodeRepayment(walletId, id) {
    amount=document.getElementById("payment-amount-"+id).value*1000*1000;
    sourceId = document.getElementById("inputWallet").value;
    postData('repayToEscrow?destinationId=' + walletId + '&sourceId=' + sourceId + '&amount=' + amount)
      .then((response) => response.text()).then((data) => {
        document.getElementById("payment-code-"+id).innerHTML = data; // JSON data parsed by `data.json()` call
      });
}