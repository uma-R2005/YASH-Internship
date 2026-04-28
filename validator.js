/**
 * Validates an email address using a basic regular expression.
 * @param {string} email - The email address to validate.
 * @returns {boolean} - True if valid, false otherwise.
 */
function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

// Example usage:
// console.log(validateEmail('test@example.com')); // true
// console.log(validateEmail('invalid-email'));    // false

module.exports = validateEmail;
