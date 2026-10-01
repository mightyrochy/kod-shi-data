# правда з фото: поле -> перелік прийнятних кодів; 'НВ' — з фото не видно; 'НЗ' — поле до речі не застосовне
# поля: slot item_type length sleeve neckline cut fabric pattern color shine metal set_parts ; деталь + ключі
НВ, НЗ = 'НВ', 'НЗ'
П = {}
def р(н, slot, item_type, length, sleeve, neckline, cut, fabric, pattern, color, shine, metal, set_parts, деталь, ключі, прим=''):
    П[н] = dict(slot=slot, item_type=item_type, length=length, sleeve=sleeve, neckline=neckline, cut=cut, fabric=fabric,
                pattern=pattern, color=color, shine=shine, metal=metal, set_parts=set_parts, деталь=деталь, ключі=ключі, прим=прим)
р(1, ['bracelet'], ['jewelry_generic'], НЗ, НЗ, НЗ, НЗ, НЗ, НЗ, ['golden', 'pearly', 'white'], ['yes'], ['gold', 'brass'], НЗ,
  'масивні барокові перли на золотистому ланцюгу з великими ланками', ['pearl', 'baroque'])
р(2, ['top'], ['top_garment'], НВ, ['sleeveless'], ['square'], ['fitted', 'bodycon'], ['jersey', 'knitted'], ['solid'],
  ['light_blue'], ['no'], НЗ, НЗ, 'майка в рубчик з квадратним вирізом', ['square', 'rib'], 'річ заправлена — довжини не видно')
р(3, ['top'], ['shirt'], НВ, ['long'], ['shirt_collar'], ['relaxed', 'oversized'], НВ, ['stripes'], ['light_blue', 'blue', 'white'],
  ['no'], НЗ, НЗ, 'сорочка у вертикальну блакитну смужку, спущене плече', ['stripe'], 'заправлена спереду — довжини не видно')
р(4, ['top'], ['top_garment'], ['waist'], ['straps'], ['v_neck'], ['fitted'], ['knitted'], ['solid'],
  ['cream', 'beige', 'milky', 'creamy', 'sand'], ['no'], НЗ, НЗ, "в'язаний укорочений топ-бралет на тонких бретелях, відкрита спина",
  ['crop', 'knit', 'strap'])
р(5, ['top'], ['top_garment'], НЗ, ['long'], ['round'], ['bodycon', 'fitted'], ['jersey', 'stretch', 'elastane'], ['solid'],
  ['powder_pink', 'pink', 'soft_pink', 'powder'], ['no'], НЗ, НЗ, 'боді з довгим рукавом, широкий овальний виріз, корсетний шов під грудьми',
  ['bodysuit', 'body'], 'другий кадр картки — чужа річ (пасок із золотою пряжкою)')
р(6, ['top'], ['sweater', 'knitwear'], ['mid_thigh'], ['short'], ['round'], ['straight', 'regular', 'relaxed'], ['knitted', 'wool'],
  ['solid'], ['taupe', 'beige', 'latte', 'sand', 'mocha'], ['no'], НЗ, НЗ, "в'язаний джемпер з коротким рукавом", ['short sleeve', 'knit'])
р(7, ['top'], ['top_garment', 'vest'], ['mid_thigh'], ['sleeveless'], ['v_neck', 'deep_v'], ['fitted', 'peplum'], НВ, ['solid'],
  ['brown', 'chocolate', 'cocoa'], ['no'], ['silver', 'steel', 'none'], НЗ, 'подовжений корсетний топ на блискавці спереду',
  ['zip', 'corset'])
р(8, ['top'], ['sweater', 'knitwear'], ['mid_thigh'], ['long'], ['round'], ['relaxed', 'regular', 'straight'], ['knitted', 'wool'],
  ['solid'], ['milky', 'cream', 'white', 'creamy'], ['no'], НЗ, НЗ, "пухнастий в'язаний светр з круглим вирізом", ['knit'])
р(9, ['outerwear'], ['jacket'], ['waist', 'mid_thigh'], ['long'], ['shirt_collar'], ['straight', 'regular', 'relaxed'],
  ['faux_leather'], ['solid'], ['chocolate', 'brown', 'cocoa'], ['yes'], ['silver', 'steel', 'none'], НЗ,
  'шкіряний бомбер з відкладним коміром і великими накладними кишенями з клапанами', ['pocket', 'collar'])
р(10, ['outerwear'], ['jacket'], ['mid_thigh'], ['long'], НЗ, ['belted', 'relaxed', 'straight'], НВ, ['solid'],
  ['beige', 'sand', 'latte', 'taupe'], ['yes', 'no'], НЗ, НЗ, 'стьобана куртка з фігурною стьожкою, капюшоном і кулісою на талії',
  ['quilt', 'hood', 'drawstring'], 'капюшон — коду вирізу нема')
р(11, ['outerwear'], ['jacket'], ['mid_thigh'], ['long'], ['shirt_collar'], ['belted', 'fitted'], ['leather', 'faux_leather', 'patent_leather'],
  ['solid'], ['black'], ['yes'], ['none', 'silver', 'steel'], НЗ, 'шкіряна куртка-сорочка з паском і чотирма накладними кишенями',
  ['belt', 'pocket'], 'кадри 2–4 картки — інша куртка (кемел, двобортна з кулісою)')
р(12, ['shoes'], ['pumps', 'dress_shoes'], НЗ, НЗ, НЗ, НЗ, ['leather', 'patent_leather'], ['animal_print', 'solid'], ['red', 'cherry'],
  ['yes'], ['silver', 'steel', 'none'], НЗ, 'металізовані червоні човники з тисненням під крокодила, шпилька', ['croc', 'metallic'])
р(13, ['shoes'], ['pumps', 'dress_shoes'], НЗ, НЗ, НЗ, НЗ, ['leather', 'faux_leather'], ['solid'], ['black'], ['yes', 'no'],
  ['silver', 'steel'], НЗ, 'човники з металевими заклепками по всьому верху, фігурний низький каблук-рюмочка', ['stud', 'rivet', 'embellish'])
р(14, ['shoes'], ['plimsolls', 'sneakers'], НЗ, НЗ, НЗ, НЗ, ['suede', 'nubuck'], ['solid'], ['cream', 'milky', 'white', 'creamy', 'beige'],
  ['no'], ['none'], НЗ, 'низькі ретро-кеди із замші з перфорацією', ['suede', 'perforat', 'retro'])
р(15, ['shoes'], ['boots'], ['knee'], НЗ, НЗ, НЗ, ['leather'], ['solid'], ['black'], ['yes', 'no'], ['none'], НЗ,
  'високі чоботи до коліна в стилі для верхової їзди на пласкій масивній підошві', ['knee', 'riding', 'flat'])
р(16, ['shoes'], ['loafers'], НЗ, НЗ, НЗ, НЗ, ['suede'], ['solid'], ['black'], ['no'], ['gold', 'brass'], НЗ,
  'замшеві лофери з золотистим трензелем (horsebit)', ['horsebit', 'bit', 'hardware'])
р(17, ['shoes'], ['ugg_boots'], ['ankle'], НЗ, НЗ, НЗ, ['suede'], ['solid'], ['camel', 'brown', 'ginger', 'sand'], ['no'], ['none'], НЗ,
  'уги-тапки на платформі з вишитою тасьмою по краю', ['platform', 'embroider', 'trim'])
р(18, ['headwear'], [], НЗ, НЗ, НЗ, НЗ, ['knitted', 'wool'], ['solid'], ['burgundy', 'cherry', 'plum'], ['no'], ['none'], НЗ,
  "в'язана шапка-біні в рубчик з відворотом", ['rib', 'cuff', 'beanie'], 'коду для шапки нема: чесно лише unknown')
р(19, ['ring'], ['ring'], НЗ, НЗ, НЗ, НЗ, НЗ, НЗ, ['black', 'golden'], ['yes'], ['gold', 'brass'], НЗ,
  'каблучка з чорним чотирилисником у золотій «зернистій» оправі з камінцем посередині', ['clover', 'quatrefoil', 'alhambra', 'onyx'])
р(20, ['set'], ['two_piece_set', 'casual_suit', 'suit'], ['midi'], ['long'], ['v_neck'], ['relaxed', 'a-line', 'straight'],
  ['knitted', 'boucle', 'tweed'], ['solid'], ['pink', 'rose', 'plum', 'lilac', 'powder_pink', 'raspberry'], ['no'], ['none'],
  [['sweater', 'knitwear', 'top_garment'], ['skirt']], 'меланжевий твідовий трикотаж з необробленим бахромчастим краєм: светр з V-вирізом і спідниця міді',
  ['fring', 'raw', 'tweed', 'boucle', 'melange'])
р(21, ['set'], ['suit'], НЗ, ['long'], НЗ, ['oversized', 'double-breasted', 'relaxed', 'straight'], НВ, ['solid'],
  ['chocolate', 'brown', 'cocoa'], ['no'], ['none'], [['blazer'], ['trousers']],
  'оверсайз двобортний піджак з виразними плечима і прямі штани', ['double-breasted', 'double breasted', 'shoulder'], 'лацкани — коду вирізу нема')
р(22, ['necklace'], ['jewelry_generic'], НЗ, НЗ, НЗ, НЗ, НЗ, НЗ, ['golden'], ['yes'], ['gold', 'brass'], НЗ,
  'щільний плаский ланцюг-змійка з вузлом', ['snake', 'herringbone', 'knot', 'chain'])
р(23, ['bottom'], ['jeans'], ['maxi'], НЗ, НЗ, ['wide', 'straight'], ['denim'], ['solid'], ['light_blue', 'denim_blue', 'blue'], ['no'],
  ['none'], НЗ, 'широкі джинси світлого прання', ['wide'])
р(24, ['bottom'], ['trousers'], ['maxi'], НЗ, НЗ, ['tapered', 'straight', 'skinny'], НВ, ['solid'], ['black'], ['no'], ['none'], НЗ,
  'класичні вузькі штани зі стрілками до щиколотки', ['crease', 'pressed', 'slim', 'tapered', 'cigarette'])
р(25, ['bottom'], ['trousers'], ['maxi', 'midi'], НЗ, НЗ, ['culottes', 'wide'], ['linen'], ['solid'], ['light_blue'], ['no'], ['none'], НЗ,
  'широкі кюлоти з високою посадкою і защипами', ['culotte', 'wide', 'pleat', 'tuck'])
р(26, ['bottom'], ['trousers'], ['maxi'], НЗ, НЗ, ['wide', 'straight'], ['satin', 'atlas', 'silk'], ['solid'], ['black'], ['yes'], ['none'],
  НЗ, 'атласні штани на резинці', ['satin', 'silk', 'elastic'])
р(27, ['bottom'], ['trousers'], ['maxi'], НЗ, НЗ, ['wide'], ['suede', 'velour'], ['solid'], ['taupe', 'mocha', 'brown', 'cocoa', 'latte'],
  ['no'], ['none'], НЗ, 'широкі штани з тканини під замшу', ['suede', 'wide'])
р(28, ['bottom'], ['trousers'], ['maxi'], НЗ, НЗ, ['wide', 'straight'], ['satin', 'atlas', 'silk', 'viscose'],
  ['geometric', 'abstract', 'print_generic'], ['brown', 'ginger', 'orange', 'terracotta'], ['yes'], ['none'], НЗ,
  'широкі штани з яскравим геометричним принтом (коричневий, помаранч, синій) на резинці', ['geometric', 'print'],
  'назва каже «жовтий» — на фото жовтого нема')
р(29, ['belt'], [], НЗ, НЗ, НЗ, НЗ, ['satin', 'atlas'], ['solid'], ['taupe', 'beige', 'grey', 'sand', 'latte'], ['yes'], ['none'], НЗ,
  "широкий атласний пасок на зав'язках, оздоблений пір'ям", ['feather'], 'коду типу «пасок» нема: чесно лише unknown')
р(30, ['necklace'], ['jewelry_generic'], НЗ, НЗ, НЗ, НЗ, НЗ, НЗ, ['silvery'], ['yes'], ['silver'], НЗ,
  'тонкий ланцюжок з кількома дрібними підвісами', ['pendant', 'charm'])
р(31, ['earrings'], ['jewelry_generic'], НЗ, НЗ, НЗ, НЗ, НЗ, НЗ, ['silvery', 'black'], ['yes'], ['silver'], НЗ,
  'сережка-кільце з великим гранованим чорним каменем', ['stone', 'crystal', 'hoop', 'huggie'])
р(32, ['dress'], ['sundress', 'dress_generic'], ['midi'], ['straps', 'sleeveless'], ['square'], ['a-line', 'full', 'fitted'],
  ['cotton', 'batiste'], ['embroidery', 'floral', 'lace_motif'], ['white', 'milky'], ['no'], ['none'], НЗ,
  'білий бавовняний сарафан з вишивкою і чорною стрічкою, протягнутою крізь мереживну прошву, бантики на бретелях',
  ['ribbon', 'bow', 'black trim', 'embroider'])
р(33, ['dress'], ['dress_generic', 'sundress'], ['maxi', 'midi'], ['sleeveless'], ['round'], ['relaxed', 'shift', 'a-line', 'straight'], НВ,
  ['abstract', 'floral', 'print_generic'], ['beige', 'camel', 'sand', 'latte', 'peach'], ['no'], ['none'], НЗ,
  'довга сукня без рукавів з великим абстрактним рослинним принтом і воланом по низу, кишені', ['print', 'flounce', 'ruffle', 'tier'])
р(34, ['dress'], ['dress_generic'], ['mini'], ['sleeveless'], ['strapless'], ['fitted', 'full'], НВ, ['solid'], ['black'], ['no'], ['none'],
  НЗ, 'сукня-бюстьє зі збіркою (шеринг) і пишною спідницею-балоном', ['bubble', 'puffball', 'balloon', 'smock', 'shirr'])
р(35, ['dress'], ['dress_generic'], ['knee'], ['long'], ['v_neck', 'shirt_collar'], ['a-line', 'fitted'], ['satin', 'atlas', 'silk'], ['solid'],
  ['powder_pink', 'pink', 'soft_pink', 'pearly', 'powder'], ['yes'], ['none'], НЗ,
  'атласна сукня з рядом дрібних перлинних ґудзиків, рукави-ліхтарики, збірка на талії ззаду', ['button', 'balloon', 'puff', 'bishop', 'shirr'])
р(36, ['dress'], ['evening_dress', 'dress_generic'], ['maxi'], ['sleeveless'], ['round'], ['shift', 'straight', 'relaxed', 'a-line'],
  ['chiffon'], ['solid'], ['black'], ['yes', 'no'], ['none'], НЗ, 'прозорий шар органзи до підлоги поверх короткої сукні-футляра',
  ['organza', 'sheer', 'transparent', 'layer'], 'органзи в переліку тканин нема — найближче chiffon')
р(37, ['bag'], ['backpack'], НЗ, НЗ, НЗ, НЗ, ['leather', 'faux_leather'], ['solid'], ['milky', 'cream', 'white', 'creamy'], ['no'],
  ['silver', 'steel'], НЗ, 'невеликий рюкзак з передньою кишенею на блискавці', ['front pocket', 'zip pocket', 'pocket'])
р(38, ['bag'], ['tote', 'bag_generic', 'hobo_bag'], НЗ, НЗ, НЗ, НЗ, ['leather'], ['solid'], ['navy', 'blue'], ['yes', 'no'],
  ['silver', 'steel'], НЗ, "м'яка велика сумка-шопер з бічними блискавками, в комплекті косметичка й плечовий ремінь",
  ['pouch', 'zip', 'strap'])
р(39, ['bag'], ['tote', 'bag_generic'], НЗ, НЗ, НЗ, НЗ, ['leather'], ['solid'], ['taupe', 'beige', 'grey', 'sand', 'latte'], ['no'], ['none'],
  НЗ, 'шопер з геометричних трикутних панелей (складаний «пазл»)', ['geometric', 'fold', 'triangle', 'panel'],
  'на фото сіро-бежевий, не молочний')
р(40, ['scarf'], ['scarf_generic', 'stole'], НЗ, НЗ, НЗ, НЗ, ['knitted', 'openwork', 'wool'], ['solid'], ['milky', 'cream', 'white', 'creamy'],
  ['no'], ['none'], НЗ, "великий широкий шарф фактурної ґратчастої в'язки", ['textur', 'waffle', 'lattice', 'knit'])
р(41, ['outerwear'], ['jacket'], ['waist', 'mid_thigh'], ['long'], ['stand_collar'], ['relaxed', 'straight'], [], ['solid'],
  ['grey', 'light_blue'], ['no'], ['none'], НЗ, 'коротка куртка з кучерявого штучного хутра (тедді) зі стійкою',
  ['sherpa', 'teddy', 'shearling', 'fleece', 'curly', 'faux fur'], 'на кадрах сіро-блакитна і біла; бежевої нема. Тканини «тедді» в переліку нема')
р(42, ['top', 'outerwear'], ['blazer'], ['mid_thigh'], ['long'], НЗ, ['oversized', 'relaxed', 'straight'], НВ, ['solid'], ['black'], ['no'],
  ['none'], НЗ, 'оверсайз однобортний жакет на один ґудзик з виразними плечима', ['shoulder', 'oversized', 'single', 'one button'],
  'лацкани — коду вирізу нема')
р(43, ['bottom'], ['skirt'], ['midi', 'maxi'], НЗ, НЗ, ['bias-slip', 'straight', 'pencil'], ['satin', 'atlas', 'silk'], ['solid'],
  ['lemon', 'yellow', 'cream'], ['yes'], ['none'], НЗ, 'атласна спідниця-сліп', ['satin', 'slip'])
р(44, ['outerwear', 'top'], ['jacket', 'hoodie'], ['waist', 'mid_thigh'], ['long'], ['round'], ['oversized', 'relaxed'], ['jersey', 'knitted'],
  ['solid'], ['beige', 'cream', 'milky', 'sand', 'creamy'], ['no'], ['none'], НЗ,
  'бомбер з щільного трикотажу на блискавці з рубчастими манжетами й низом, кишені в швах', ['zip', 'rib'])
р(45, ['bottom'], ['trousers', 'loungewear', 'sportswear'], ['maxi'], НЗ, НЗ, ['tapered', 'relaxed'], ['velour', 'velvet'], ['solid'],
  ['grey', 'graphite', 'taupe'], ['yes', 'no'], ['none'], НЗ, 'велюрові штани-джогери на манжетах', ['velour', 'velvet', 'cuff', 'jogger'],
  'на кадрах сірі й мокко; хутра з фото не видно')
р(46, ['bottom'], ['jeans'], ['maxi'], НЗ, НЗ, ['tapered', 'straight', 'relaxed'], ['denim'], ['solid'], ['black'], ['no'], ['none'], НЗ,
  'джинси мом з високою посадкою, звужені донизу', ['mom', 'high', 'tapered'], 'перший кадр чорні, далі сині')
р(47, ['dress'], ['dress_generic'], ['mini', 'mid_thigh'], ['three_quarter', 'elbow'], ['off_shoulder'], ['a-line', 'full', 'fitted'], НВ,
  ['floral'], ['white', 'milky'], ['no'], ['none'], НЗ, 'квіткова сукня з відкритими плечима на резинці з зав\'язкою, волани на рукавах і по низу',
  ['off-shoulder', 'off the shoulder', 'elastic', 'ruffle', 'flounce', 'tier'], 'перший кадр білий з квітами, далі блакитний')
р(48, ['bottom'], ['skirt'], ['knee'], НЗ, НЗ, ['pencil', 'straight'], НВ, ['solid'], ['grey'], ['no'], ['none'], НЗ,
  'спідниця-олівець до коліна з діагональним розрізом спереду', ['slit'])
р(49, ['outerwear'], ['coat'], ['midi'], ['long'], ['stand_collar', 'round'], ['belted', 'straight'], НВ, ['solid'],
  ['beige', 'camel', 'sand', 'latte'], ['yes'], ['none'], НЗ, 'довге стьобане пальто ромбом з поясом', ['quilt', 'diamond', 'belt'],
  'слот у каталозі «пояс» — це пальто; фото — селфі в примірочній, два однакові кадри')
р(50, ['top'], ['shirt'], ['mid_thigh'], ['long'], ['shirt_collar'], ['oversized', 'relaxed'], НВ, ['solid'], ['white'], ['no'], ['none'], НЗ,
  'сорочка з подовженими широкими манжетами, нагрудна кишеня, спущене плече', ['cuff'])
р(51, ['outerwear'], ['coat'], ['maxi', 'midi'], ['long'], НЗ, ['belted', 'wrap', 'oversized', 'relaxed'], НВ, ['solid'],
  ['camel', 'beige', 'sand', 'latte', 'ginger'], ['no'], ['none'], НЗ, 'довге пальто на запах з поясом, широкі лацкани',
  ['wrap', 'belt', 'long'], 'слот у каталозі «пояс» — це пальто; кадри кемел і чорне')
р(52, ['top'], ['top_garment', 'knitwear', 'sweater'], НВ, ['long'], ['turtleneck', 'stand_collar', 'round'], ['fitted', 'bodycon'],
  ['jersey', 'knitted', 'stretch'], ['solid'], ['brown', 'chocolate', 'cocoa'], ['no'], ['none'], НЗ,
  'облягаючий тонкий трикотажний джемпер з драпуванням на грудях і напівпрозорими рукавами, комір-стійка',
  ['ruch', 'gather', 'drape', 'sheer', 'mesh'], 'заправлений — довжини не видно')
р(53, ['top'], ['hoodie', 'sweater', 'knitwear', 'sportswear'], ['mid_thigh'], ['long'], ['round'], ['oversized', 'relaxed'],
  ['jersey', 'cotton', 'knitted'], ['stripes'], ['milky', 'white', 'cream'], ['no'], ['none'], НЗ,
  'світшот у горизонтальну чорну смужку з чорними рубчастими горловиною, манжетами й низом', ['stripe', 'cuff', 'rib'])
р(54, ['dress'], ['dress_generic'], ['mini', 'mid_thigh'], ['short', 'cap'], ['off_shoulder'], ['a-line', 'full', 'relaxed', 'shift'], НВ,
  ['solid'], ['light_blue'], ['no'], ['none'], НЗ, 'ярусна сукня-трапеція з відкритими плечима на резинці з рюшем',
  ['off-shoulder', 'off the shoulder', 'elastic', 'tier', 'ruffle', 'flounce'], 'кадри блакитна, синя, рожева')
р(55, ['top', 'outerwear'], ['blazer'], ['mid_thigh'], ['long'], НЗ, ['double-breasted', 'relaxed', 'oversized', 'straight'], НВ, ['solid'],
  ['black'], ['no'], ['none'], НЗ, 'двобортний жакет', ['double-breasted', 'double breasted'], 'лацкани — коду вирізу нема')
р(56, ['top'], ['t_shirt', 'top_garment'], ['mid_thigh'], ['long'], ['round'], ['relaxed', 'straight', 'oversized'], ['jersey', 'cotton'],
  ['solid'], ['beige', 'latte', 'sand', 'taupe'], ['no'], ['none'], НЗ, 'лонгслів з необробленим (відкритим) зрізом горловини, спущене плече',
  ['raw', 'unfinished', 'cut edge'], 'кадри бежевий і ліловий')
р(57, ['outerwear'], ['vest'], ['waist', 'mid_thigh'], ['sleeveless', 'cap'], ['stand_collar'], ['relaxed', 'oversized', 'straight'], НВ,
  ['solid'], ['black'], ['yes', 'no'], ['none'], НЗ, 'стьобаний жилет-бомбер з хвилястою стьожкою, коміром-стійкою і кулісою по низу',
  ['quilt', 'stand collar', 'high collar', 'drawstring'])
р(58, ['dress'], ['dress_generic'], ['mini', 'mid_thigh', 'knee'], ['short'], ['stand_collar', 'turtleneck'], ['shift', 'straight'],
  ['suede', 'velour'], ['solid'], ['light_blue'], ['no'], ['none'], НЗ, 'пряма сукня з тканини під замшу з коміром-стійкою і коротким рукавом',
  ['suede', 'mock', 'stand collar', 'high neck'], 'кадри блакитна, бежева, бірюзова')
р(59, ['bottom'], ['jeans'], НВ, НЗ, НЗ, ['straight', 'wide', 'relaxed'], ['denim'], ['solid'], ['milky', 'cream', 'white', 'creamy', 'beige'],
  ['no'], ['none'], НЗ, 'джинси кольору екрю з контрастною коричневою відстрочкою і шкіряною нашивкою', ['contrast', 'stitch', 'patch'],
  'один кадр — лише сідниці зблизька: довжини не видно')
р(60, ['bottom'], ['shorts'], ['mid_thigh', 'mini'], НЗ, НЗ, ['pleated', 'wide', 'straight', 'relaxed'], НВ, ['solid'],
  ['brown', 'chocolate', 'mocha', 'cocoa'], ['no'], ['none'], НЗ, 'костюмні шорти з високою посадкою і защипами', ['pleat', 'tuck'],
  'кадри коричневі й кремові')
# ── уточнення правди волокном, яке називає текст і з яким фото не сперечається ──
for н, поле, дод in [(2, 'fabric', ['cotton']), (3, 'fabric', ['cotton']), (4, 'fabric', ['cotton']), (5, 'fabric', ['polyester']),
                     (8, 'fabric', ['acrylic']), (10, 'fabric', ['polyester']), (20, 'fabric', ['wool']),
                     (21, 'fabric', ['wool', 'viscose', 'polyester']), (24, 'fabric', ['polyester', 'viscose', 'elastane']),
                     (25, 'fabric', ['cotton']), (26, 'fabric', ['polyester']), (27, 'fabric', ['polyester', 'cotton', 'viscose']),
                     (34, 'fabric', ['cotton']), (36, 'fabric', ['viscose']), (40, 'fabric', ['acrylic']), (6, 'sleeve', ['elbow']),
                     (9, 'cut', ['fitted']), (27, 'cut', ['straight'])]:
    П[н][поле] = (П[н][поле] if isinstance(П[н][поле], list) else []) + дод
П[38]['fabric'] = ['faux_leather']; П[13]['fabric'] = ['leather']; П[32]['ключі'] += ['velvet']
for н, з in П.items():                                  # метал одягу: «нема металу» — правда, а не «не застосовне»
    if з['metal'] == НЗ and з['slot'][0] not in ('bracelet', 'ring', 'necklace', 'earrings'):
        з['metal'] = ['none']
# ── що каже ТЕКСТ крамниці (назва, категорія крамниці, опис, параметри), кодами; поля, про які текст мовчить, — нема ──
Т = {
 1: dict(slot='bracelet', color='golden', metal='gold'),
 2: dict(slot='top', item_type='top_garment', sleeve='sleeveless', neckline='square', fabric='cotton', color='light_blue'),
 3: dict(slot='top', item_type='shirt', sleeve='long', cut='oversized', fabric='cotton', pattern='stripes', color='light_blue'),
 4: dict(slot='top', item_type='top_garment', length='waist', sleeve='straps', neckline='round', fabric='cotton', color='cream'),
 5: dict(slot='top', item_type='top_garment', fabric='polyester', color='powder'),
 6: dict(slot='top', item_type='sweater', length='mid_thigh', sleeve='elbow', neckline='round', cut='straight', fabric='wool', color='beige'),
 7: dict(slot='top', item_type='top_garment', color='brown'),
 8: dict(slot='top', item_type='sweater', fabric='knitted', color='milky'),
 9: dict(slot='outerwear', item_type='jacket', cut='straight', fabric='faux_leather', color='chocolate'),
 10: dict(slot='outerwear', item_type='jacket', cut='belted', fabric='polyester', color='beige'),
 11: dict(slot='outerwear', item_type='jacket', fabric='leather'),
 12: dict(slot='shoes', item_type='dress_shoes', fabric='leather', color='red'),
 13: dict(slot='shoes', item_type='dress_shoes', fabric='leather', color='black'),
 14: dict(slot='shoes', item_type='plimsolls', color='milky'),
 15: dict(slot='shoes', item_type='boots', fabric='leather', color='black'),
 16: dict(slot='shoes', item_type='loafers', fabric='suede', color='black', metal='gold'),
 17: dict(slot='shoes', item_type='ugg_boots', color='beige'),
 18: dict(slot='headwear', fabric='wool', color='burgundy'),
 19: dict(slot='ring', item_type='ring'),
 20: dict(slot='set', item_type='suit', neckline='v_neck', cut='relaxed', fabric='wool', set_parts=[['sweater'], ['skirt']]),
 21: dict(slot='set', item_type='suit', cut='straight', fabric='wool', color='chocolate', set_parts=[['blazer'], ['trousers']]),
 22: dict(slot='necklace', color='golden', metal='gold'),
 23: dict(slot='bottom', item_type='jeans', cut='wide', fabric='denim', color='light_blue'),
 24: dict(slot='bottom', item_type='trousers', cut='tapered', fabric='polyester', color='black'),
 25: dict(slot='bottom', item_type='trousers', cut='culottes', fabric='linen', color='light_blue'),
 26: dict(slot='bottom', item_type='trousers', cut='straight', fabric='silk', color='black'),
 27: dict(slot='bottom', item_type='trousers', cut='wide', fabric='polyester', color='beige'),
 28: dict(slot='bottom', item_type='trousers', color='yellow'),
 29: dict(slot='belt', color='taupe'),
 30: dict(slot='necklace', color='silvery', metal='silver'),
 31: dict(slot='earrings', color='silvery', metal='silver'),
 32: dict(slot='dress', item_type='sundress', length='midi', fabric='cotton', pattern='embroidery', color='white'),
 33: dict(slot='dress', color='beige'),
 34: dict(slot='dress', length='mini', neckline='off_shoulder', cut='fitted', fabric='cotton', color='black'),
 35: dict(slot='dress', color='pink'),
 36: dict(slot='dress', length='maxi', cut='relaxed', fabric='viscose', color='black'),
 37: dict(slot='bag', item_type='backpack', fabric='leather', color='milky'),
 38: dict(slot='bag', fabric='faux_leather', color='blue'),
 39: dict(slot='bag', item_type='tote', fabric='leather', color='milky'),
 40: dict(slot='scarf', item_type='scarf_generic', fabric='wool', color='white'),
 41: dict(slot='outerwear', item_type='jacket', color='beige'),
 42: dict(slot='top', item_type='blazer', color='black'),
 43: dict(slot='bottom', item_type='skirt', length='midi', fabric='satin', color='lemon'),
 44: dict(slot='outerwear', item_type='jacket', color='beige'),
 45: dict(slot='bottom', item_type='trousers', fabric='velour', color='grey'),
 46: dict(slot='bottom', item_type='jeans', fabric='denim', color='black'),
 47: dict(slot='dress', pattern='floral', color='white'),
 48: dict(slot='bottom', item_type='skirt', length='knee', color='grey'),
 49: dict(slot='outerwear', item_type='coat', cut='belted', color='beige'),
 50: dict(slot='top', item_type='shirt', color='white'),
 51: dict(slot='outerwear', item_type='coat', cut='wrap', color='black'),
 52: dict(slot='top', item_type='sweater', fabric='jersey', color='brown'),
 53: dict(slot='top', pattern='stripes', color='milky'),
 54: dict(slot='dress', length='mini', neckline='off_shoulder', color='light_blue'),
 55: dict(slot='top', item_type='blazer', cut='double-breasted', color='black'),
 56: dict(slot='top', item_type='t_shirt', sleeve='long', color='beige'),
 57: dict(slot='outerwear', item_type='vest', color='black'),
 58: dict(slot='dress', sleeve='short', fabric='suede', color='light_blue'),
 59: dict(slot='bottom', item_type='jeans', cut='straight', fabric='denim', color='milky'),
 60: dict(slot='bottom', item_type='shorts', cut='pleated', color='brown'),
}
# опора тексту — УСІ коди, які текст підтримує (перший — те, що текст стверджує про річ; решта — варіанти/склад)
ОПОРА_ДОД = {
 2: dict(fabric=['elastane', 'knitted', 'jersey']), 3: dict(cut=['relaxed']), 4: dict(fabric=['knitted', 'jersey']),
 5: dict(color=['powder_pink', 'pink'], fabric=['elastane', 'stretch']), 6: dict(fabric=['viscose', 'polyamide', 'knitted'], color=['taupe']),
 8: dict(fabric=['wool', 'acrylic', 'polyamide']), 9: dict(cut=['fitted'], fabric=['polyester']), 11: dict(fabric=['faux_leather']),
 18: dict(fabric=['knitted']), 20: dict(cut=['a-line'], fabric=['polyester', 'knitted']), 21: dict(fabric=['viscose', 'polyester']),
 24: dict(fabric=['viscose', 'elastane']), 25: dict(fabric=['cotton']), 26: dict(color=['grey']),
 27: dict(cut=['straight'], fabric=['cotton', 'viscose'], color=['brown']), 35: dict(color=['pearly', 'powder_pink', 'soft_pink']),
 40: dict(fabric=['acrylic', 'knitted', 'openwork']), 41: dict(color=['grey']), 45: dict(color=['beige']), 46: dict(color=['blue']),
 47: dict(color=['light_blue']), 48: dict(color=['beige']), 49: dict(color=['black']), 50: dict(color=['light_blue']),
 51: dict(color=['beige']), 54: dict(color=['blue']), 56: dict(color=['black']), 57: dict(color=['beige']), 58: dict(color=['blue']),
 60: dict(color=['mocha']), 34: dict(cut=['full']), 36: dict(fabric=['chiffon']),
}
ОПОРА = {н: {к: ([в] if isinstance(в, str) else в) for к, в in т.items()} for н, т in Т.items()}
for н, д in ОПОРА_ДОД.items():
    for к, в in д.items():
        ОПОРА[н][к] = ОПОРА[н].get(к, []) + в
# поле «матеріал» theoriginals: #1 «мідь; перли» (золотиста мідь), #19 «жовте золото 750, діамант, онікс»
П[1]['metal'] = ['gold', 'brass', 'copper']; Т[1]['metal'] = 'copper'; ОПОРА[1]['metal'] = ['copper', 'gold']
Т[19]['metal'] = 'gold'; ОПОРА[19]['metal'] = ['gold']; П[19]['metal'] = ['gold']
Т[22]['metal'] = 'gold'
# ── рядок features розбору MamayLM (г): чи названо головну деталь з фото; вигадка — твердження, якого нема ні в тексті
#    крамниці, ні на фото (або яке фото спростовує). Суддя — очима, рядок поруч із фото й текстом.
F = {
 1: (True, 'solid brass body (текст: мідь)'), 2: (True, 'three quarter sleeves (це майка без рукавів)'), 3: (True, None),
 4: (True, None), 5: (True, None), 6: (False, None), 7: (True, None), 8: (True, None),
 9: (True, 'ribbed cuffs and hem (у тексті нема, на фото — шкіряний край)'), 10: (True, None), 11: (False, None), 12: (False, None),
 13: (True, 'block heel (текст: незвичайна форма, 5 см; фото — рюмочка)'), 14: (False, None), 15: (False, None), 16: (True, None),
 17: (False, None), 18: (True, None), 19: (True, None), 20: (False, 'ribbed finish (фото: бахромчастий необроблений край)'),
 21: (True, 'non-stretchable (склад має 5% лайкри)'), 22: (False, None), 23: (True, 'zipper and button closure (у тексті нема)'),
 24: (True, None), 25: (True, None), 26: (True, None), 27: (True, None), 28: (False, None), 29: (False, None), 30: (False, None),
 31: (False, 'monobracelet (текст і фото: моно-сережка)'), 32: (True, 'velvet trim on the bottom (оздоба на ліфі, не внизу)'),
 33: (False, 'spaghetti straps and v-neckline (фото: без рукавів, круглий виріз; текст мовчить)'), 34: (True, None), 35: (False, None),
 36: (True, None), 37: (False, 'adjustable shoulder strap, pocket on the back (у тексті нема — вгадано)'),
 38: (False, 'magnetic clasp (фото: блискавка; текст мовчить)'), 39: (False, None), 40: (True, None),
 41: (False, 'faux fur collar, teddy lining, zip pockets (текст — лише назва; фото: тедді зовні, кишень на блискавці не видно)'),
 42: (True, None), 43: (True, None), 44: (False, 'three-thread fleece inside (текст — лише назва)'), 45: (True, None),
 46: (True, 'straight cut (мом — звужені; текст — лише назва)'), 47: (False, None), 48: (True, None),
 49: (False, 'stepped hem, belt with buckle (фото: пояс на зав\'язку; текст — лише назва)'), 50: (True, None),
 51: (False, 'double-breasted, two side pockets (пальто на запах; текст — лише назва)'), 52: (False, None), 53: (True, None),
 54: (False, 'two-piece set, double elastic straps, American crepe (сукня; текст — лише назва)'), 55: (True, None),
 56: (False, 'high collar, open front with ties, raw edges at hem and sleeves (необроблений лише виріз)'),
 57: (True, 'lacquered fabric (текст — лише назва)'), 58: (True, None), 59: (False, None),
 60: (False, 'denim fabric (текст: з костюмки), straight cut (фото: защипи)'),
}
for н in (1, 19, 22, 30, 31):                           # загальний слот прикрас — не помилка, лише менш точний
    П[н]['slot'] = П[н]['slot'] + ['jewelry']
П[6]['metal'] = НВ                                      # «невелика металева фурнітура» з фото не видна
