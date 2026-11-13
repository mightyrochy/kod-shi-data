/* Рука кожного образу й фото кожної картки — службове (наряд Стенд-як-людина-рука-образу, рядки 15122–15123). Беремо з самої
   сторінки, без правки продукту: `ЗБ.ключ[поз]` — рука, що дала картку `#к-<поз>` (ключ перемішано сідом входу
   `ЗБ.вхід_рук.сід`), `ЗБ.діагноз` «control · hand_2_broken=…» і `ЗБ.поломка` — назва поломки руки 2, `img` у `.ф` і
   `.річ` — що картка справді показала. Пише лише у службові файли ситуації: жінка й суддя цього не читають. */
async function знімокРук(стор){
  return стор.evaluate(() => {
    if (typeof ЗБ === 'undefined' || !ЗБ || !ЗБ.ключ) return null;
    const рядок = (т, н) => String(т == null ? '' : т).replace(/\s+/g, ' ').trim().slice(0, н || 120);
    const стан = і => ({src: і.getAttribute('src') || '', завантажено: !!(і.complete && і.naturalWidth > 0), w: і.naturalWidth || 0,
                        h: і.naturalHeight || 0, завершено: !!і.complete, lazy: і.loading === 'lazy'});
    const картки = Array.from(document.querySelectorAll('[id^="к-"]')).filter(е => /^к-\d+$/.test(е.id));
    const зЗБ = поз => ((ЗБ.картки || [])[поз] || null);
    const позиції = картки.map((к, н) => {
      const поз = Number(к.id.slice(2)), дані = (typeof П !== 'undefined' && П && (П.картки || [])[поз]) || зЗБ(поз) || {};
      const вих = (дані.речі || []).map(х => ({ід: х && х.id || '', фото: (х && х.фото) ? String(х.фото).slice(0, 300) : null,
                                              кадрів: ((х && х.фото_усі) || []).filter(Boolean).length}));
      const фо = Array.from(к.querySelectorAll('.ф')).map(ф => {
        const і = ф.querySelector('img'), в = вих.find(х => х.ід === (ф.dataset.id || ''));
        /* мертвий кадр замінено силуетом — адреси в DOM нема, лишається та, що в даних картки */
        return {ід: ф.dataset.id || '', ...(і ? стан(і) : {силует: true, src: '', завантажено: false, w: 0}), src_дані: в ? в.фото : null};
      });
      const речі = Array.from(к.querySelectorAll('.річ')).map(о => {
        const і = о.querySelector('img.мініатюра');
        return {назва: рядок((о.querySelector('.н') || о).innerText, 80), слот: о.dataset.слот || '',
                мініатюра: і ? стан(і) : null};
      });
      return {позиція: н + 1, ід_картки: к.id, рука: (ЗБ.ключ || [])[поз] || null, ф: фо, речі, дані_речей: вих};
    });
    const діагн = (ЗБ.діагноз || []).filter(д => /hand_2_broken|control ·/.test(д)).map(д => рядок(д, 300));
    return {сід: ЗБ.вхід_рук ? ЗБ.вхід_рук.сід : null, ключ: (ЗБ.ключ || []).join(''),
            прогін: (typeof П !== 'undefined' && П && П.прогін) || null,
            поломка_руки_2: {діагноз: діагн, що: ЗБ.поломка ? рядок(JSON.stringify(ЗБ.поломка), 400) : null,
                             контроль: ЗБ.контроль ? ЗБ.контроль.поломка || null : null},
            готово: !!ЗБ.готово, позиції};
  }).catch(() => null);
}
/* Усі фото карток — зараз, не коли дійде прокрутка (`loading="lazy"`): так «не завантажилось» не плутається з «не доскролила». */
async function доЗавантажитиФото(стор){
  await стор.evaluate(() => { document.querySelectorAll('[id^="к-"] img').forEach(і => { if (і.loading === 'lazy') і.loading = 'eager'; }); }).catch(() => {});
}
module.exports = {знімокРук, доЗавантажитиФото};
