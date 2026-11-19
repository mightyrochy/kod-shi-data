function запуститиП(){
  return старт().catch(e => {
    ЗАПУЩЕНО = false;
    показатиЗбійЗапису('profile_unreadable', e);
  });
}
запуститиП();
