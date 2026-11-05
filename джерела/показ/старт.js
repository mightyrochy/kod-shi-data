$('збій-прибрати').onclick = () => { $('збій-стан').textContent = ''; };
function запуститиП(){
  return старт().catch(e => {
    ЗАПУЩЕНО = false;
    збійЖінціП($('збій-стан'), 'profile_unreadable', e);
  });
}
window.addEventListener('hashchange', запуститиП);
запуститиП();
