/*
 * Example 1: Math calculation utility
 */
function calculateCircleArea(radius) {
    // Check for negative radius
    if (radius <= 0) {
        return 0;
    }
    const PI = 3.14159;
    /* Return calculated area */
    return PI * radius * radius;
}
