// Math and string utility helpers

/**
 * Returns a random number between min and max.
 * @param {number} min - minimum value (inclusive)
 * @param {number} max - maximum value (inclusive)
 * @returns {number}
 */
export function randomRange(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Generates a standard random UUID (v4-ish placeholder for client-side).
 * @returns {string}
 */
export function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Formats currency values in USD.
 * @param {number} value
 * @returns {string}
 */
export function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

/**
 * Formats carbon values with metric tonnes (t) and two decimal places.
 * @param {number} value - Carbon in kg
 * @returns {string}
 */
export function formatCarbon(value) {
  const tonnes = value / 1000;
  return `${tonnes.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} t`;
}
