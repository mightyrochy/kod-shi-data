// джерела/проби/очікування.js
// Єдине очікування для проб (3.4-Е, за зразком чекатиСтан у аудит/проби/рв6_стенд.js з 3.4-Д).

/**
 * Очікування стану сторінки з єдиним форматом діагностики таймауту.
 *
 * @param {import('playwright').Page} стор
 * @param {string} назва Назва очікуваного стану для діагностики та звіту
 * @param {Function|string|{подія?: string, локатор?: any, стан?: string}} умова
 * @param {any} [арг] Аргумент для передачі у функцію умови
 * @param {number} [таймаут=30000]
 * @param {{polling?: number|string, можеНеСтатись?: boolean}} [опції={}]
 */
async function чекатиСтан(стор, назва, умова, арг, таймаут = 30000, опції = {}) {
  const параметри = { timeout: таймаут };
  if (опції.polling) параметри.polling = опції.polling;
  try {
    if (умова && умова.подія) return await стор.waitForEvent(умова.подія, параметри);
    if (умова && умова.локатор) return await умова.локатор.waitFor({ state: умова.стан || 'visible', timeout: таймаут });
    return await стор.waitForFunction(умова, арг, параметри);
  } catch (err) {
    if (опції.можеНеСтатись) return false;
    throw new Error('ТАЙМАУТ очікування стану «' + назва + '» (' + таймаут + ' мс): ' + String(err.message).split('\n')[0]);
  }
}

/**
 * Перевірка видимості елемента в DOM за селектором:
 * ненульова рамка й visibility !== 'hidden' (як видимість у Playwright).
 *
 * @param {string} в Селектор елемента
 * @returns {boolean}
 */
const ВИДНО_ЕЛЕМЕНТ = в => {
  const е = document.querySelector(в);
  if (!е) return false;
  const р = е.getBoundingClientRect();
  return р.width > 0 && р.height > 0 && getComputedStyle(е).visibility !== 'hidden';
};

module.exports = {
  чекатиСтан,
  ВИДНО_ЕЛЕМЕНТ,
};
