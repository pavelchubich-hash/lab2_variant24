// Example 2: User profile processor
const user = {
    firstName: "Pavel",
    lastName: "Chubich",
    age: 20, // Age in years
    skills: ["Python", "JavaScript", "SQL"]
};

function formatUser(u) {
    /* Compose display text */
    var fullName = u.firstName + " " + u.lastName;
    return fullName + " (" + u.skills.length + " skills)";
}
