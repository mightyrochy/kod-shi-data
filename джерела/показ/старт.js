function запуститиП(){
  return старт().catch(e => {
    ЗАПУЩЕНО = false;
    збійЖінціП($('збій-стан'), 'profile_unreadable', e);
  });
}
запуститиП();
