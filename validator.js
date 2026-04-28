/**
 * Validates an email address using a basic regular expression.
 * @param {string} email - The email address to validate.
 * @returns {boolean} - True if valid, false otherwise.
 */
function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

/**
 * Validates a phone number using a basic regular expression.
 * Supports various formats like +1234567890, (123) 456-7890, 123-456-7890.
 * @param {string} phoneNumber - The phone number to validate.
 * @returns {boolean} - True if valid, false otherwise.
 */
function validatePhoneNumber(phoneNumber) {
  const regex = /^(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}$/;
  return regex.test(phoneNumber);
}

module.exports = {
  validateEmail,
  validatePhoneNumber,
};
