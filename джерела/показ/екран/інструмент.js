/* ── КАРТКА РЕЗУЛЬТАТУ ІНСТРУМЕНТА (частина 7ґ; доти — `інструменти.js`) ── вузол під реплікою; логіка дає запис
   результату кодами (`tool`, `done`, `збій`, `знайдено`), слова складає картка. */
/* Збій інструмента — сталим написом свого виду; «не знайшла» — ід, якого вже нема серед збережених. */
const ЗБІЙ_ІНСТРУМЕНТА_П = {save_scenario: 'not_saved', list_scenarios: 'scenarios_unreadable',
                            open_scenario: 'library_unreadable', delete_scenario: 'not_deleted', new_scenario: 'not_written',
                            switch_profile: 'profile_unreadable', confirm_case: 'not_written',
                            set_weather_feel: 'not_written', find_item: 'catalogue_search_failed'};
/* Картка результату під реплікою: підпис — той самий, що показує кнопка вікна; назва — її ввід (`назва`), без
   назви — підпис без назви з датою (`підписБезНазвиП`), як у «Збережених». */
function карткаІнструментаП(р){
  const к = ел('div', 'картка-інструмента');
  const назва = {назва: р.name || підписБезНазвиП(р.час)};
  if (р.tool === 'save_scenario' && р.done)
    текстЖінціП(к, підписЗНазвоюП(['Сценарій збережено як «', назва, '».']), 'tool_scenario_saved_failed');
  else if (р.tool === 'list_scenarios' && р.done){
    /* рядки — записи «Збережених» (`усіСценарії`) за ід результату, тими самими кнопками; видалений відтоді рядка не
       має, а збій читання — рядок збою під заголовком */
    const іди = р.scenarios || [];
    текстЖінціП(к.appendChild(ел('div')), р.кількість ? 'Збережені сценарії — ' + р.кількість + ':' : 'Збережених сценаріїв ще нема.', 'tool_scenarios_failed');
    if (іди.length) (async () => {
      try{
        const список = await усіСценарії();
        список.forEach(с => {
          if (!іди.includes(с.ід)) return;
          const н = ел('b'); назваСценаріюП(н, с.назва, с.час);
          к.appendChild(кнопкаСценаріюП(с, н));
        });
      }catch(e){ збійЖінціП(к.appendChild(ел('div')), 'scenarios_unreadable', e); }
    })();
  }
  else if (р.tool === 'open_scenario' && р.done)
    текстЖінціП(к, підписЗНазвоюП(['Відкрито сценарій «', назва, '».']), 'tool_scenario_opened_failed');
  else if (р.tool === 'delete_scenario' && р.done)
    текстЖінціП(к, підписЗНазвоюП(['Сценарій «', назва, '» видалено.']), 'tool_scenario_deleted_failed');
  else if (р.tool === 'new_scenario' && р.done)
    текстЖінціП(к, 'Почато новий сценарій.');
  else if (р.tool === 'switch_profile' && р.done)
    текстЖінціП(к, підписЗНазвоюП(['Відкрито профіль «', {назва: р.name || підписПрофілюП(р.номер)}, '».']), 'profile_unreadable');
  else if (р.tool === 'confirm_case' && р.done)
    текстЖінціП(к, 'Розуміння нагоди підтверджено.');
  else if (р.tool === 'set_weather_feel' && р.done)
    текстЖінціП(к, 'Погода: ' + (ВІДЧУТТЯ_П[р.feel] || р.feel) + '.', 'tool_weather_failed');
  else if (р.tool === 'find_item' && р.done){
    /* рядок речі — той самий, що в пари під ціною каблука (`рядокЗмінноїПари`: мініатюра, назва-посилання, крамниця ·
       ціна), у порядку, в якому код їх радить; нема жодної — карти без рядків: «нема» каже репліка */
    (р.варіанти || []).forEach(в => к.appendChild(рядокЗмінноїПари(в)));
  }
  else if (р.tool === 'switch_profile' && р.збій === 'profile_not_found')
    збійЖінціП(к, 'profile_not_found', 'tool_failed: ' + р.tool);
  else if (р.tool === 'switch_profile' && р.збій === 'profile_switch_blocked')
    збійЖінціП(к, 'profile_switch_blocked', 'tool_failed: ' + р.tool);
  else if (р.знайдено === false) збійЖінціП(к, 'scenario_not_found', 'tool_failed: ' + р.tool);
  else збійЖінціП(к, ЗБІЙ_ІНСТРУМЕНТА_П[р.tool] || 'not_written', 'tool_failed: ' + р.tool);
  return к;
}
