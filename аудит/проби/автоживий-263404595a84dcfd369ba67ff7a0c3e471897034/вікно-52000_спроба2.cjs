/* Лише налаштування прогону №2865: однакове вікно сторінки та рушія.
   NODE_OPTIONS обгортки з --disable-gpu зберігається. Записувач задає CTX=57344
   перед дочірнім процесом; цей preload виставляє потрібне нарядом значення
   до читання CTX проксі та стендом. Фактичний контекст підтверджує HTTP API. */
if (process.env.SCENA === 'б1_концерт_стримано' && process.env.MODEL_CTX === '52000') {
  process.env.CTX = JSON.stringify({'qwen/qwen3.5-9b': 52000,
    'mamaylm-gemma-3-12b-it-v2.0': 16384});
  process.env.ZAPYS_VYKLYKIV = require('path').join(__dirname, 'б1_концерт_стримано', 'виклики_моста.jsonl');
}
