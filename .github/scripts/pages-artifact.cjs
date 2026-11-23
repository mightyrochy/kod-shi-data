// Pages отримує ID з upload-pages-artifact: повтор запуску не вибирає старий однойменний файл.
const НЕВДАЛІ = new Set([
  'deployment_failed', 'deployment_perms_error', 'deployment_content_failed',
  'deployment_cancelled', 'deployment_lost'
]);

module.exports = async function опублікувати({github, context, core, artifactId,
  чекати = мс => new Promise(resolve => setTimeout(resolve, мс)), тепер = Date.now, таймаут = 600000}) {
  const ід = Number(artifactId);
  if (!Number.isSafeInteger(ід) || ід <= 0) throw new Error('Нема коректного ID завантаженого артефакту');
  const адреса = '/repos/{owner}/{repo}/pages/deployments';
  const репо = context.repo;
  const {data: випуск} = await github.request('POST ' + адреса, {
    ...репо, artifact_id: ід, pages_build_version: context.sha, oidc_token: await core.getIDToken()
  });
  const deployment_id = випуск.id || випуск.status_url?.split('/').pop() || context.sha;
  core.info('Pages: артефакт ' + ід + ', випуск ' + deployment_id);
  const початок = тепер();
  let завершено = false, збоїв = 0;
  try {
    while (тепер() - початок < таймаут) {
      let стан;
      try {
        ({data: стан} = await github.request('GET ' + адреса + '/{deployment_id}', {...репо, deployment_id}));
        збоїв = 0;
      } catch (помилка) {
        if ((помилка.status !== 404 && !(помилка.status >= 500)) || ++збоїв >= 10) throw помилка;
        core.warning('Тимчасово не прочитано стан Pages: ' + помилка.message);
        await чекати(5000);
        continue;
      }
      core.info('Стан Pages: ' + стан.status);
      if (стан.status === 'succeed') {
        завершено = true;
        core.setOutput('page_url', випуск.page_url);
        core.setOutput('status', 'succeed');
        return;
      }
      if (НЕВДАЛІ.has(стан.status)) {
        завершено = true;
        throw new Error('Розгортання Pages не виконано: ' + стан.status);
      }
      await чекати(5000);
    }
    throw new Error('Pages не завершив розгортання за відведений час');
  } catch (помилка) {
    if (!завершено) {
      try { await github.request('POST ' + адреса + '/{deployment_id}/cancel', {...репо, deployment_id}); }
      catch (скасування) { core.warning('Не вдалося скасувати випуск Pages: ' + скасування.message); }
    }
    throw помилка;
  }
};
