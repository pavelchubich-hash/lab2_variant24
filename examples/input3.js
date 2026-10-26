/*
 * Example 3: Array filtering and mapping pipeline
 */
function processScores(scores) {
    // Filter out scores below threshold
    var valid = scores.filter(function(score) {
        return score >= 50;
    });

    // Normalize valid scores
    return valid.map(function(item) {
        return item * 2;
    });
}
