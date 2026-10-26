/*
 * Example 5: Task status evaluator
 */
function evaluateStatus(code, isTriggered) {
    // Determine status description based on code
    var resultText = "pending";
    if (code === 1 && isTriggered === 1) {
        resultText = "active_triggered";
    } else if (code === 2) {
        /* Finished status */
        resultText = "completed";
    }
    return resultText;
}
