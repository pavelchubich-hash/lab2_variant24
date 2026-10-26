// Example 4: Asynchronous request simulator
function requestData(endpoint, timeout) {
    /* Initiate asynchronous operation */
    return new Promise(function(resolve, reject) {
        if (!endpoint) {
            reject("Invalid endpoint");
            return;
        }
        // Simulated delayed response
        setTimeout(function() {
            resolve({ status: 200, url: endpoint });
        }, timeout);
    });
}
