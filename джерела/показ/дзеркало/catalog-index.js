"use strict";

// Пошук у фіді, вкладеному в робочу HTML-збірку. Ідентифікатори збігаються з ідентифікаторами рушія.
window.MirrorIndex = (() => {
  const initialCount = 28890; // Значення з build_index.py.
  const assetName = "catalog.json.gz";
  function unavailable(reason) {
    const error = new Error(reason);
    error.name = "MirrorCatalogueError";
    return error;
  }
  const stop = new Set(("а або б будь в від ви до для за знайди знайти з зі і із й із яку який які мені менше мій моя на недорого ніж " +
    "одну під покажи пошук річ речі та у хочу шукаю щось як гривень гривні грн").split(/\s+/u));
  // Найпоширеніші назви речей і відтінків мають різні закінчення, форми й магазинні написання.
  const aliases = [
    [/^(?:джинс[иіаух]?|jeans)$/u,"джинси"], [/^(?:штан|брюк|брюч|pants|trousers)/u,"штани"],
    [/^(?:спідниц|спідниць|skirt)/u,"спідниця"], [/^(?:лег[іи]н|лосин|leggings)/u,"легінси"],
    [/^(?:сукн|сукон|платт|dress)/u,"сукня"], [/^(?:сарафан|sundress)/u,"сарафан"],
    [/^(?:блуз|blouse)/u,"блуза"], [/^(?:сорочк|сорочо|сорочц|shirt$)/u,"сорочка"],
    [/^(?:футбол|футболок|tee$|tshirt)/u,"футболка"], [/^(?:светр|светер|светрів|sweater)/u,"светр"],
    [/^(?:жакет|блейзер|піджак|blazer)/u,"жакет"], [/^(?:пальт|coat$)/u,"пальто"],
    [/^(?:куртк|курто|куртц|jacket)/u,"куртка"], [/^(?:кардиган|cardigan)/u,"кардиган"],
    [/^(?:черевик|череви[цч]|ankleboot)/u,"черевики"], [/^(?:кросів|кросово|снікер|sneaker)/u,"кросівки"],
    [/^(?:лофер|loafer)/u,"лофери"], [/^(?:кед[аиіоу]?|кедів|кедах)$/u,"кеди"],
    [/^(?:сумк|сумок|сумц|bag$|handbag)/u,"сумка"], [/^(?:клатч|clutch)/u,"клатч"],
    [/^(?:хустк|хусто|хустц)/u,"хустка"], [/^(?:сережк|сережок|сережц|earring)/u,"сережки"],
    [/^(?:шарф|scarf)/u,"шарф"], [/^(?:костюм|suit$)/u,"костюм"],
    [/^(?:взуття|взуттям|взутті|shoes?|footwear)$/u,"взуття"],
    [/^(?:біл(?:ий|а|е|у|і|их|ою|ого|ому|им|ими)$|white$)/u,"білий"], [/^(?:чорн|black$)/u,"чорний"], [/^(?:сіри|сіра|сіре|сірі|сіро|gray$|grey$)/u,"сірий"],
    [/^(?:блакит|голуб|azure$)/u,"блакитний"], [/^(?:син(?:ій|я|і|є|ю|іх|ім|ьою|ього|ьому|іми|ий)$|navy$|blue$)/u,"синій"],
    [/^(?:борд|бургунд|марсал|burgundy$|bordeaux$)/u,"бордо"], [/^(?:шокол|chocol|мокко|mocha)/u,"шоколад"],
    [/^(?:коричн|brown$)/u,"коричневий"], [/^(?:беж|beige$)/u,"бежевий"], [/^(?:зел[еє]н|green$)/u,"зелений"],
    [/^(?:червон|red$)/u,"червоний"], [/^(?:рожев|pink$)/u,"рожевий"], [/^(?:жовт|yellow$)/u,"жовтий"],
    [/^(?:молоч|молоко$|milk$)/u,"молочний"], [/^(?:айворі|ivory$)/u,"айворі"],
    [/^(?:сріб|silver$)/u,"срібний"], [/^(?:золот|gold$)/u,"золотий"],
    [/^(?:шкір|leather$)/u,"шкіра"], [/^(?:лля|льон|льня|linen$)/u,"льон"], [/^(?:бавовн|котон|cotton$)/u,"бавовна"],
    [/^(?:шерст|вовн|wool$)/u,"вовна"], [/^(?:замш|suede$)/u,"замша"], [/^(?:трикотаж|knit$)/u,"трикотаж"],
    [/^(?:замок|блискавк|zipper$)/u,"блискавка"], [/^(?:рукав|sleeve)/u,"рукав"], [/^(?:посадк|посадц|посадок)/u,"посадка"]
  ];
  const lexicon = new Map();
  function normalized(text) {
    return String(text || "").normalize("NFKC").toLocaleLowerCase("uk").replace(/\u0301/gu,"")
      .replace(/[’'ʼ`]/gu,"").replace(/ґ/gu,"г");
  }
  function wordKey(word) {
    if (lexicon.has(word)) return lexicon.get(word);
    const alias = aliases.find(([pattern]) => pattern.test(word));
    let key = alias ? alias[1] : word;
    if (!alias && /^[а-яєії]+$/u.test(word) && word.length > 4) {
      key = word.replace(/(?:овими|евими|овому|евому|ього|ого|ому|ими|ою|ею|ий|ій|ів|їв|ях|ах|их|ніх|ої|еї|ова|ові|е|і|и|а|я|у|ю)$/u,"");
      if (key.length < 3) key = word;
    }
    lexicon.set(word,key);
    return key;
  }
  function tokens(text, removeFillers = false) {
    const raw = normalized(text).match(/[a-zа-яєії0-9]+/gu) || [];
    return [...new Set(raw.filter(w => w.length > 1 && (!removeFillers || (!stop.has(w) && !/^жіноч/u.test(w)))).map(wordKey))];
  }
  function prepareQuery(query) {
    let minimum = 0, maximum = Infinity;
    const normalizedQuery = normalized(query);
    const rest = normalizedQuery.replace(/(?:^|\s)(від|дорожче|до|дешевше|не дорожче)\s*(?:ніж\s*)?(\d{1,7}(?:[ \u00a0\u202f]\d{3})*(?:[.,]\d{1,2})?)(?:\s*(?:₴|грн\.?|гривень))?/gu,
      (_,op,value) => {
        const amount = Number(value.replace(/\s/gu,"").replace(",","."));
        if (op === "від" || op === "дорожче") minimum = Math.max(minimum,amount);
        else maximum = Math.min(maximum,amount);
        return " ";
      });
    return {words:tokens(rest,true),minimum,maximum};
  }
  const encodeTerms = text => "|" + tokens(text).join("|") + "|";

  async function openSnapshot() {
    let response;
    try {
      response = await fetch(window.MirrorFiles?.[assetName] || assetName);
    } catch {
      throw unavailable("Не вдалося завантажити каталог. Відкрий сайт або автономний файл Люстерка й повтори пошук.");
    }
    if (!response.ok) throw unavailable("Не вдалося завантажити каталог. Спробуй ще раз.");
    const bytes = new Uint8Array(await response.arrayBuffer());
    let json;
    try {
      if (bytes[0] === 0x1f && bytes[1] === 0x8b) {
        if (typeof DecompressionStream !== "function") throw unavailable("Для пошуку в каталозі потрібна новіша версія браузера.");
        const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
        json = await new Response(stream).json();
      } else {
        // HTTP-сервер може розпакувати gzip у шарі Content-Encoding.
        json = JSON.parse(new TextDecoder().decode(bytes));
      }
    } catch(error) {
      if (error?.name === "MirrorCatalogueError") throw error;
      throw unavailable("Не вдалося прочитати каталог. Спробуй повторно відкрити Люстерко.");
    }
    if (!json.meta || !Array.isArray(json.rows) || json.rows.length !== json.meta.count) {
      throw unavailable("Файл каталогу неповний. Відкрий його повторно.");
    }
    const byId = new Map();
    for (const row of json.rows) {
      byId.set(row[0],row);
      const split = row[0].indexOf("@");
      if (split > 0) byId.set(row[0].slice(0,split),row);
    }
    return {rows:json.rows,meta:json.meta,byId,lexical:null};
  }
  let loaded, loading;
  function store() {
    if (loaded) return Promise.resolve(loaded);
    if (!loading) {
      loading = openSnapshot().then(db => { loaded=db; return db; }).finally(() => { loading=null; });
    }
    return loading;
  }
  function asProduct(row) {
    if (!row) return null;
    const [id,name,slot,slotLabel,shop,price,color,hue,url,photos,tagText,material,available,sourceDate,inEngine] = row;
    return {id,offerId:id.split("@")[0],name,slot,slotLabel,shop,price,currency:"UAH",color,hue,url,
      image:photos[0] || "",photos:[...photos],tags:tagText.split(" ").filter(Boolean),material,available,sourceDate,inEngine};
  }
  async function get(id) {
    if (typeof id !== "string" || !id) return null;
    const db=await store();
    return asProduct(db.byId.get(id));
  }
  // Коли людина уже друкує, довгий перший пошук не повинен зупиняти поле вводу.
  async function buildLexical(rows) {
    const index=[];
    let started=Date.now();
    for (let i=0;i<rows.length;i++) {
      const [,name,,slotLabel,shop,,,hue,,,tagText,material]=rows[i];
      index.push([encodeTerms(name+" "+shop+" "+hue),encodeTerms(slotLabel+" "+tagText+" "+material)]);
      if (i%128===127 && Date.now()-started>12 && typeof setTimeout==="function") {
        await new Promise(resolve=>setTimeout(resolve,0));
        started=Date.now();
      }
    }
    return index;
  }
  function score(primary,detail,token) {
    const start="|"+token;
    if(primary.includes(start+"|")) return 6;
    if(detail.includes(start+"|")) return 3;
    if(token.length>2 && primary.includes(start)) return 2;
    if(token.length>2 && detail.includes(start)) return 1;
    return 0;
  }
  function naturalInteger(value, fallback, maximum) {
    if (value==null || !Number.isFinite(Number(value))) return fallback;
    return Math.min(maximum,Math.max(0,Math.floor(Number(value))));
  }
  async function search(query="", options={}) {
    const db=await store();
    const {words,minimum,maximum}=prepareQuery(query);
    const offset=naturalInteger(options?.offset,0,Number.MAX_SAFE_INTEGER);
    const limit=naturalInteger(options?.limit,36,500);
    const slot=options?.slot;
    const availableOnly=options?.availableOnly===true;
    const priceFilter=minimum>0 || maximum<Infinity;
    if(!words.length && !priceFilter && !slot && !availableOnly) {
      return {results:db.rows.slice(offset,offset+limit).map(asProduct),total:db.rows.length,offset,limit};
    }
    if(words.length && !db.lexical) db.lexical=buildLexical(db.rows);
    const index=words.length ? await db.lexical : null;
    const matches=[];
    for(let i=0;i<db.rows.length;i++) {
      const row=db.rows[i],price=row[5];
      if(slot && slot!==row[2] && slot!==row[3]) continue;
      if(availableOnly && row[12]!==true) continue;
      if(priceFilter && (price==null || price<minimum || price>maximum)) continue;
      let rank=0, matched=true;
      for(const word of words) {
        const weight=score(index[i][0],index[i][1],word);
        if(!weight) {matched=false; break;}
        rank+=weight;
      }
      if(matched) matches.push({i,rank:rank*5+Number(row[12]===true)*2+Number(Boolean(row[9].length))});
    }
    matches.sort((a,b)=>b.rank-a.rank || a.i-b.i);
    return {results:matches.slice(offset,offset+limit).map(x=>asProduct(db.rows[x.i])),total:matches.length,offset,limit};
  }
  return {search,get,get count(){return loaded?.meta.count || initialCount;},get metadata(){return loaded?.meta || null;}};
})();
