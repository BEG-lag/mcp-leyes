# Demo transcript

Recorded on 2026-11-17 with `uv run python scripts/demo.py --write`: a real MCP client talking to `mcp-leyes` over stdio, with the real leyes-mx history. Nothing below was edited.

First call (`list_laws`) with an empty cache, including the first sync from `https://github.com/BEG-lag/leyes-mx.git`: 7.6 s. Cache after the sync: 29 MB (375 versions, 189,611 indexed sections, leyes-mx at `43e040e`). Later calls read from the local clone and index; their timings are shown with each call.

## tools/list

`list_laws`, `get_article`, `article_history`, `diff_article`, `diff_reform`, `search`, `reforms`, `transitorios`

## list_laws

`{}` · 7.18 s · ok

````markdown
# Leyes federales disponibles

36 leyes · 375 versiones en git · versión más reciente: DOF 07-10-2026 · leyes-mx `43e040e` · sincronizado 17-11-2026 15:25 (CDMX)

## Constitución

| Abrev. | Ley | Última reforma (DOF) | Artículos | Versiones | Desde |
|---|---|---|---:|---:|---|
| CPEUM (`cpeum`) | Constitución Política de los Estados Unidos Mexicanos | 07-10-2026 | 136 | 44 | 07-04-2006 |

## Energía (reforma de 2025)

| Abrev. | Ley | Última reforma (DOF) | Artículos | Versiones | Desde |
|---|---|---|---:|---:|---|
| LSE (`lse`) | Ley del Sector Eléctrico | sin reformas | 188 | 1 | 18-03-2025 |
| LSH (`lsh`) | Ley del Sector Hidrocarburos | sin reformas | 166 | 1 | 18-03-2025 |
| LEPECFE (`lepecfe`) | Ley de la Empresa Pública del Estado, Comisión Federal de Electricidad | sin reformas | 131 | 1 | 18-03-2025 |
| LEPEPM (`lepepm`) | Ley de la Empresa Pública del Estado, Petróleos Mexicanos | sin reformas | 126 | 1 | 18-03-2025 |
| LCNE (`lcne`) | Ley de la Comisión Nacional de Energía | 26-12-2025 | 28 | 1 | 26-12-2025 |
| LPTE (`lpte`) | Ley de Planeación y Transición Energética | sin reformas | 100 | 1 | 18-03-2025 |
| LBio (`lbio`) | Ley de Biocombustibles | sin reformas | 46 | 1 | 18-03-2025 |
| LGeo (`lgeo`) | Ley de Geotermia | sin reformas | 66 | 1 | 18-03-2025 |
| LIH (`lih`) | Ley de Ingresos sobre Hidrocarburos | 28-12-2025 | 64 | 10 | 11-08-2014 |
| LANSI (`lansi`) | Ley de la Agencia Nacional de Seguridad Industrial y de Protección al Medio Ambiente del Sector Hidrocarburos | 11-05-2022 | 38 | 3 | 11-08-2014 |

## Minería, agua, tierra y ambiente

| Abrev. | Ley | Última reforma (DOF) | Artículos | Versiones | Desde |
|---|---|---|---:|---:|---|
| LMin (`lmin`) | Ley de Minería | 08-05-2023 | 79 | 4 | 26-06-2006 |
| LAN (`lan`) | Ley de Aguas Nacionales | 11-12-2025 | 215 | 11 | 29-04-2004 |
| LGAg (`lgag`) | Ley General de Aguas | sin reformas | 45 | 1 | 11-12-2025 |
| LGEEPA (`lgeepa`) | Ley General del Equilibrio Ecológico y la Protección al Ambiente | 19-01-2026 | 270 | 21 | 23-05-2006 |
| LAgra (`lagra`) | Ley Agraria | 14-11-2025 | 201 | 10 | 09-07-1993 |

## Empresa, comercio y competencia

| Abrev. | Ley | Última reforma (DOF) | Artículos | Versiones | Desde |
|---|---|---|---:|---:|---|
| CCom (`ccom`) | Código de Comercio | 18-02-2026 | 1,641 | 20 | 06-06-2006 |
| LGSM (`lgsm`) | Ley General de Sociedades Mercantiles | 26-12-2025 | 277 | 10 | 28-07-2006 |
| LGTOC (`lgtoc`) | Ley General de Títulos y Operaciones de Crédito | 26-03-2024 | 463 | 8 | 18-07-2006 |
| LIE (`lie`) | Ley de Inversión Extranjera | 27-05-2024 | 42 | 10 | 18-07-2006 |
| LFCE (`lfce`) | Ley Federal de Competencia Económica | 14-11-2025 | 153 | 4 | 23-05-2014 |
| LFPC (`lfpc`) | Ley Federal de Protección al Consumidor | 23-12-2025 | 190 | 27 | 06-06-2006 |

## Propiedad intelectual y datos personales

| Abrev. | Ley | Última reforma (DOF) | Artículos | Versiones | Desde |
|---|---|---|---:|---:|---|
| LFDA (`lfda`) | Ley Federal del Derecho de Autor | 14-05-2026 | 259 | 10 | 23-07-2003 |
| LFPPI (`lfppi`) | Ley Federal de Protección a la Propiedad Industrial | 03-04-2026 | 421 | 2 | 01-07-2020 |
| LFPDPPP (`lfpdppp`) | Ley Federal de Protección de Datos Personales en Posesión de los Particulares | 14-11-2025 | 64 | 2 | 20-03-2025 |

## Trabajo, civil, amparo y procedimiento

| Abrev. | Ley | Última reforma (DOF) | Artículos | Versiones | Desde |
|---|---|---|---:|---:|---|
| LFT (`lft`) | Ley Federal del Trabajo | 14-05-2026 | 1,266 | 14 | 17-01-2006 |
| CCF (`ccf`) | Código Civil Federal | 14-11-2025 | 3,103 | 14 | 31-12-2004 |
| LAmp (`lamp`) | Ley de Amparo, Reglamentaria de los artículos 103 y 107 de la Constitución Política de los Estados Unidos Mexicanos | 16-10-2025 | 272 | 11 | 02-04-2013 |
| CNPCF (`cnpcf`) | Código Nacional de Procedimientos Civiles y Familiares | 15-01-2026 | 1,191 | 4 | 07-06-2023 |

## Administración pública, fiscal y penal

| Abrev. | Ley | Última reforma (DOF) | Artículos | Versiones | Desde |
|---|---|---|---:|---:|---|
| LOAPF (`loapf`) | Ley Orgánica de la Administración Pública Federal | 07-05-2026 | 72 | 30 | 02-06-2006 |
| LFPA (`lfpa`) | Ley Federal de Procedimiento Administrativo | 14-11-2025 | 119 | 5 | 30-05-2000 |
| LGRA (`lgra`) | Ley General de Responsabilidades Administrativas | 15-12-2025 | 235 | 9 | 18-07-2016 |
| CFF (`cff`) | Código Fiscal de la Federación | 09-04-2026 | 421 | 27 | 12-05-2006 |
| LISR (`lisr`) | Ley del Impuesto sobre la Renta | 01-04-2024 (índice LeyesBiblio: 13-11-2026, aún no en el texto) | 236 | 7 | 11-12-2013 |
| CPF (`cpf`) | Código Penal Federal | 13-03-2026 | 556 | 36 | 30-06-2006 |
| CNPP (`cnpp`) | Código Nacional de Procedimientos Penales | 28-11-2025 | 490 | 13 | 05-03-2014 |

Usa la abreviatura o el slug en las demás herramientas. «Desde» es la versión más antigua archivada: no hay texto anterior a esa fecha.

_No oficial. Solo el DOF es fuente auténtica. No es asesoría legal. Textos: versiones consolidadas de la Cámara de Diputados vía [leyes-mx](https://github.com/BEG-lag/leyes-mx)._
````

## get_article

`{"law": "CPEUM", "article": "27", "date": "2013-01-01"}` · 0.02 s · ok

````markdown
# CPEUM · Artículo 27.

**Constitución Política de los Estados Unidos Mexicanos** › Título Primero › Capítulo I · De los Derechos Humanos y sus Garantías

Texto aplicable al 01-01-2013: versión DOF 15-10-2012 (commit [`9cdbce4`](https://github.com/BEG-lag/leyes-mx/commit/9cdbce4657f0fd3189d9b20e69314b6b7be67d0b)).

---

La propiedad de las tierras y aguas comprendidas dentro de los límites del territorio nacional, corresponde originariamente a la Nación, la cual ha tenido y tiene el derecho de transmitir el dominio de ellas a los particulares, constituyendo la propiedad privada.

Las expropiaciones sólo podrán hacerse por causa de utilidad pública y mediante indemnización.

La nación tendrá en todo tiempo el derecho de imponer a la propiedad privada las modalidades que dicte el interés público, así como el de regular, en beneficio social, el aprovechamiento de los elementos naturales susceptibles de apropiación, con objeto de hacer una distribución equitativa de la riqueza pública, cuidar de su conservación, lograr el desarrollo equilibrado del país y el mejoramiento de las condiciones de vida de la población rural y urbana. En consecuencia, se dictarán las medidas necesarias para ordenar los asentamientos humanos y establecer adecuadas provisiones, usos, reservas y destinos de tierras, aguas y bosques, a efecto de ejecutar obras públicas y de planear y regular la fundación, conservación, mejoramiento y crecimiento de los centros de población; para preservar y restaurar el equilibrio ecológico; para el fraccionamiento de los latifundios; para disponer, en los términos de la ley reglamentaria, la organización y explotación colectiva de los ejidos y comunidades; para el desarrollo de la pequeña propiedad rural; para el fomento de la agricultura, de la ganadería, de la silvicultura y de las demás actividades económicas en el medio rural, y para evitar la destrucción de los elementos naturales y los daños que la propiedad pueda sufrir en perjuicio de la sociedad.

Corresponde a la Nación el dominio directo de todos los recursos naturales de la plataforma continental y los zócalos submarinos de las islas; de todos los minerales o substancias que en vetas, mantos, masas o yacimientos, constituyan depósitos cuya naturaleza sea distinta de los componentes de los terrenos, tales como los minerales de los que se extraigan metales y metaloides utilizados en la industria; los yacimientos de piedras preciosas, de sal de gema y las salinas formadas directamente por las aguas marinas; los productos derivados de la descomposición de las rocas, cuando su explotación necesite trabajos subterráneos; los yacimientos minerales u orgánicos de materias susceptibles de ser utilizadas como fertilizantes; los combustibles minerales sólidos; el petróleo y todos los carburos de hidrógeno sólidos, líquidos o gaseosos; y el espacio situado sobre el territorio nacional, en la extensión y términos que fije el Derecho Internacional.

Son propiedad de la Nación las aguas de los mares territoriales en la extensión y términos que fije (el, sic DOF 20-01-1960) Derecho Internacional; las aguas marinas interiores; las de las lagunas y esteros que se comuniquen permanente o intermitentemente con el mar; las de los lagos interiores de formación natural que estén ligados directamente a corrientes constantes; las de los ríos y sus afluentes directos o indirectos, desde el punto del cauce en que se inicien las primeras aguas permanentes, intermitentes o torrenciales, hasta su desembocadura en el mar, lagos, lagunas o esteros de propiedad nacional; las de las corrientes constantes o interminentes (intermitentes, sic DOF 20-01-1960) y sus afluentes directos o indirectos, cuando el cauce de aquéllas en toda su extensión o en parte de ellas, sirva de límite al territorio nacional o a dos entidades federativas, o cuando pase de una entidad federativa a otra o cruce la línea divisoria de la República; la de los lagos, lagunas o esteros cuyos vasos, zonas o riberas, estén cruzadas por líneas divisorias de dos o más entidades o entre la República y un país vecino, o cuando el límite de las riberas sirva de lindero entre dos entidades federativas o a la República con un país vecino; las de los manantiales que broten en las playas, zonas marítimas, cauces, vasos o riberas de los lagos, lagunas o esteros de propiedad nacional, y las que se extraigan de las minas; y los cauces, lechos o riberas de los lagos y corrientes interiores en la extensión que fija la ley. Las aguas del subsuelo pueden ser libremente alumbradas mediante obras artificiales y apropiarse por el dueño del terreno, pero cuando lo exija el interés público o se afecten otros aprovechamientos; el Ejecutivo Federal podrá reglamentar su extracción y utilización y aún establecer zonas vedadas, al igual que para las demás aguas de propiedad nacional. Cualesquiera otras aguas no incluidas en la enumeración anterior, se considerarán como parte integrante de la propiedad de los terrenos por los que corran o en los que se encuentren sus depósitos, pero si se localizaren en dos o más predios, el aprovechamiento de estas aguas se considerará de utilidad pública, y quedará sujeto a las disposiciones que dicten los Estados.

En los casos a que se refieren los dos párrafos anteriores, el dominio de la Nación es inalienable e imprescriptible y la explotación, el uso o el aprovechamiento de los recursos de que se trata, por los particulares o por sociedades constituidas conforme a las leyes mexicanas, no podrá realizarse sino mediante concesiones, otorgadas por el Ejecutivo Federal, de acuerdo con las reglas y condiciones que establezcan las leyes. Las normas legales relativas a obras o trabajos de explotación de los minerales y substancias a que se refiere el párrafo cuarto, regularán la ejecución y comprobación de los que se efectúen o deban efectuarse a partir de su vigencia, independientemente de la fecha de otorgamiento de las concesiones, y su inobservancia dará lugar a la cancelación de éstas. El Gobierno Federal tiene la facultad de establecer reservas nacionales y suprimirlas. Las declaratorias correspondientes se harán por el Ejecutivo en los casos y condiciones que las leyes prevean. Tratándose del petróleo y de los carburos de hidrógeno sólidos, líquidos o gaseosos o de minerales radioactivos, no se otorgarán concesiones ni contratos, ni subsistirán los que en su caso se hayan otorgado y la Nación llevará a cabo la explotación de esos productos, en los términos que señale la Ley Reglamentaria respectiva. Corresponde exclusivamente a la Nación generar, conducir, transformar, distribuir y abastecer energía eléctrica que tenga por objeto la prestación de servicio público. En esta materia no se otorgarán concesiones a los particulares y la Nación aprovechará los bienes y recursos naturales que se requieran para dichos fines.

Corresponde también a la Nación el aprovechamiento de los combustibles nucleares para la generación de energía nuclear y la regulación de sus aplicaciones en otros propósitos. El uso de la energía nuclear sólo podrá tener fines pacíficos.

La Nación ejerce en una zona económica exclusiva situada fuera del mar territorial y adyacente a éste, los derechos de soberanía y las jurisdicciones que determinen las leyes del Congreso. La zona económica exclusiva se extenderá a doscientas millas náuticas, medidas a partir de la línea de base desde la cual se mide el mar territorial. En aquellos casos en que esa extensión produzca superposición con las zonas económicas exclusivas de otros Estados, la delimitación de las respectivas zonas se hará en la medida en que resulte necesario, mediante acuerdo con estos Estados.

La capacidad para adquirir el dominio de las tierras y aguas de la Nación, se regirá por las siguientes prescripciones:

I. Sólo los mexicanos por nacimiento o por naturalización y las sociedades mexicanas tienen derecho para adquirir el dominio de las tierras, aguas y sus accesiones o para obtener concesiones de explotación de minas o aguas. El Estado podrá conceder el mismo derecho a los extranjeros, siempre que convengan ante la Secretaría de Relaciones en considerarse como nacionales respecto de dichos bienes y en no invocar por lo mismo la protección de sus gobiernos por lo que se refiere a aquéllos; bajo la pena, en caso de faltar al convenio, de perder en beneficio de la Nación, los bienes que hubieren adquirido en virtud del mismo. En una faja de cien kilómetros a lo largo de las fronteras y de cincuenta en las playas, por ningún motivo podrán los extranjeros adquirir el dominio directo sobre tierras y aguas.

El Estado de acuerdo con los intereses públicos internos y los principios de reciprocidad, podrá, a juicio de la Secretaría de Relaciones, conceder autorización a los Estados extranjeros para que adquieran, en el lugar permanente de la residencia de los Poderes Federales, la propiedad privada de bienes inmuebles necesarios para el servicio directo de sus embajadas o legaciones.

II. Las asociaciones religiosas que se constituyan en los términos del artículo 130 y su ley reglamentaria tendrán capacidad para adquirir, poseer o administrar, exclusivamente, los bienes que sean indispensables para su objeto, con los requisitos y limitaciones que establezca la ley reglamentaria;

III. Las instituciones de beneficencia, pública o privada, que tengan por objeto el auxilio de los necesitados, la investigación científica, la difusión de la enseñanza, la ayuda recíproca de los asociados, o cualquier otro objeto lícito, no podrán adquirir más bienes raíces que los indispensables para su objeto, inmediata o directamente destinados a él, con sujeción a lo que determine la ley reglamentaria;

IV. Las sociedades mercantiles por acciones podrán ser propietarias de terrenos rústicos pero únicamente en la extensión que sea necesaria para el cumplimiento de su objeto.

En ningún caso las sociedades de esta clase podrán tener en propiedad tierras dedicadas a actividades agrícolas, ganaderas o forestales en mayor extensión que la respectiva equivalente a veinticinco veces los límites señalados en la fracción XV de este artículo. La ley reglamentaria regulará la estructura de capital y el número mínimo de socios de estas sociedades, a efecto de que las tierras propiedad de la sociedad no excedan en relación con cada socio los límites de la pequeña propiedad. En este caso, toda propiedad accionaria individual, correspondiente a terrenos rústicos, será acumulable para efectos de cómputo. Asimismo, la ley señalará las condiciones para la participación extranjera en dichas sociedades.

La propia ley establecerá los medios de registro y control necesarios para el cumplimiento de lo dispuesto por esta fracción;

V. Los bancos debidamente autorizados, conforme a las leyes de instituciones de crédito, podrán tener capitales impuestos, sobre propiedades urbanas y rústicas de acuerdo con las prescripciones de dichas leyes, pero no podrán tener en propiedad o en administración más bienes raíces que los enteramente necesarios para su objeto directo.

VI. Los estados y el Distrito Federal, lo mismo que los municipios de toda la República, tendrán plena capacidad para adquirir y poseer todos los bienes raíces necesarios para los servicios públicos.

Las leyes de la Federación y de los Estados en sus respectivas jurisdicciones, determinarán los casos en que sea de utilidad pública la ocupación de la propiedad privada, y de acuerdo con dichas leyes la autoridad administrativa hará la declaración correspondiente. El precio que se fijará como indemnización a la cosa expropiada, se basará en la cantidad que como valor fiscal de ella figure en las oficinas catastrales o recaudadoras, ya sea que este valor haya sido manifestado por el propietario o simplemente aceptado por él de un modo tácito por haber pagado sus contribuciones con esta base. El exceso de valor o el demérito que haya tenido la propiedad particular por las mejoras o deterioros ocurridos con posterioridad a la fecha de la asignación del valor fiscal, será lo único que deberá quedar sujeto a juicio pericial y a resolución judicial. Esto mismo se observará cuando se trate de objetos cuyo valor no esté fijado en las oficinas rentísticas.

El ejercicio de las acciones que corresponden a la Nación, por virtud de las disposiciones del presente artículo, se hará efectivo por el procedimiento judicial; pero dentro de este procedimiento y por orden de los tribunales correspondientes, que se dictará en el plazo máximo de un mes, las autoridades administrativas procederán desde luego a la ocupación, administración, remate o venta de las tierras o aguas de que se trate y todas sus accesiones, sin que en ningún caso pueda revocarse lo hecho por las mismas autoridades antes que se dicte sentencia ejecutoriada.

VII. Se reconoce la personalidad jurídica de los núcleos de población ejidales y comunales y se protege su propiedad sobre la tierra, tanto para el asentamiento humano como para actividades productivas.

La ley protegerá la integridad de las tierras de los grupos indígenas.

La ley, considerando el respeto y fortalecimiento de la vida comunitaria de los ejidos y comunidades, protegerá la tierra para el asentamiento humano y regulará el aprovechamiento de tierras, bosques y aguas de uso común y la provisión de acciones de fomento necesarias para elevar el nivel de vida de sus pobladores.

La ley, con respeto a la voluntad de los ejidatarios y comuneros para adoptar las condiciones que más les convengan en el aprovechamiento de sus recursos productivos, regulará el ejercicio de los derechos de los comuneros sobre la tierra y de cada ejidatario sobre su parcela. Asimismo establecerá los procedimientos por los cuales ejidatarios y comuneros podrán asociarse entre sí, con el Estado o con terceros y otorgar el uso de sus tierras; y, tratándose de ejidatarios, transmitir sus derechos parcelarios entre los miembros del núcleo de población; igualmente fijará los requisitos y procedimientos conforme a los cuales la asamblea ejidal otorgará al ejidatario el dominio sobre su parcela. En caso de enajenación de parcelas se respetará el derecho de preferencia que prevea la ley.

Dentro de un mismo núcleo de población, ningún ejidatario podrá ser titular de más tierra que la equivalente al 5% del total de las tierras ejidales. En todo caso, la titularidad de tierras en favor de un solo ejidatario deberá ajustarse a los límites señalados en la fracción XV.

La asamblea general es el órgano supremo del núcleo de población ejidal o comunal, con la organización y funciones que la ley señale. El comisariado ejidal o de bienes comunales, electo democráticamente en los términos de la ley, es el órgano de representación del núcleo y el responsable de ejecutar las resoluciones de la asamblea.

La restitución de tierras, bosques y aguas a los núcleos de población se hará en los términos de la ley reglamentaria;

VIII. Se declaran nulas:

a) Todas las enajenaciones de tierras, aguas y montes pertenecientes a los pueblos, rancherías, congregaciones o comunidades, hechas por los jefes políticos, Gobernadores de los Estados, o cualquiera otra autoridad local en contravención a lo dispuesto en la Ley de 25 de junio de 1856 y demás leyes y disposiciones relativas;

b) Todas las concesiones: composiciones o ventas de tierras, aguas y montes, hechas por las Secretarías de Fomento, Hacienda o cualquiera otra autoridad federal, desde el día primero de diciembre de 1876, hasta la fecha, con las cuales se hayan invadido y ocupado ilegalmente los ejidos, terrenos de común repartimiento o cualquiera otra clase, pertenecientes a los pueblos, rancherías, congregaciones o comunidades, y núcleos de población.

c) Todas las diligencias de apeo o deslinde, transacciones, enajenaciones o remates practicados durante el período de tiempo a que se refiere la fracción anterior, por compañías, jueces u otras autoridades de los Estados o de la Federación, con los cuales se hayan invadido u ocupado ilegalmente tierras, aguas y montes de los ejidos, terrenos de común repartimiento, o de cualquiera otra clase, pertenecientes a núcleos de población.

Quedan exceptuadas de la nulidad anterior, únicamente las tierras que hubieren sido tituladas en los repartimientos hechos con apego a la Ley de 25 de junio de 1856 y poseídas en nombre propio a título de dominio por más de diez años cuando su superficie no exceda de cincuenta hectáreas.

IX. La división o reparto que se hubiere hecho con apariencia de legítima entre los vecinos de algún núcleo de población y en la que haya habido error o vicio, podrá ser nulificada cuando así lo soliciten las tres cuartas partes de los vecinos que estén en posesión de una cuarta parte de los terrenos, materia de la división, o una cuarta parte de los mismos vecinos cuando estén en posesión de las tres cuartas partes de los terrenos.

X. (Se deroga)

XI. (Se deroga)

XII. (Se deroga)

XIII. (Se deroga)

XIV. (Se deroga)

XV. En los Estados Unidos Mexicanos quedan prohibidos los latifundios.

Se considera pequeña propiedad agrícola la que no exceda por individuo de cien hectáreas de riego o humedad de primera o sus equivalentes en otras clases de tierras.

Para los efectos de la equivalencia se computará una hectárea de riego por dos de temporal, por cuatro de agostadero de buena calidad y por ocho de bosque, monte o agostadero en terrenos áridos.

Se considerará, asimismo, como pequeña propiedad, la superficie que no exceda por individuo de ciento cincuenta hectáreas cuando las tierras se dediquen al cultivo de algodón, si reciben riego; y de trescientas, cuando se destinen al cultivo del plátano, caña de azúcar, café, henequén, hule, palma, vid, olivo, quina, vainilla, cacao, agave, nopal o árboles frutales.

Se considerará pequeña propiedad ganadera la que no exceda por individuo la superficie necesaria para mantener hasta quinientas cabezas de ganado mayor o su equivalente en ganado menor, en los términos que fije la ley, de acuerdo con la capacidad forrajera de los terrenos.

Cuando debido a obras de riego, drenaje o cualesquiera otras ejecutadas por los dueños o poseedores de una pequeña propiedad se hubiese mejorado la calidad de sus tierras, seguirá siendo considerada como pequeña propiedad, aún cuando, en virtud de la mejoría obtenida, se rebasen los máximos señalados por esta fracción, siempre que se reúnan los requisitos que fije la ley.

Cuando dentro de una pequeña propiedad ganadera se realicen mejoras en sus tierras y éstas se destinen a usos agrícolas, la superficie utilizada para este fin no podrá exceder, según el caso, los límites a que se refieren los párrafos segundo y tercero de esta fracción que correspondan a la calidad que hubieren tenido dichas tierras antes de la mejora;

XVI. (Se deroga)

XVII. El Congreso de la Unión y las legislaturas de los estados, en sus respectivas jurisdicciones, expedirán leyes que establezcan los procedimientos para el fraccionamiento y enajenación de las extensiones que llegaren a exceder los límites señalados en las fracciones IV y XV de este artículo.

El excedente deberá ser fraccionado y enajenado por el propietario dentro del plazo de un año contado a partir de la notificación correspondiente. Si transcurrido el plazo el excedente no se ha enajenado, la venta deberá hacerse mediante pública almoneda. En igualdad de condiciones, se respetará el derecho de preferencia que prevea la ley reglamentaria.

Las leyes locales organizarán el patrimonio de familia, determinando los bienes que deben constituirlo, sobre la base de que será inalienable y no estará sujeto a embargo ni a gravamen ninguno;

XVIII. Se declaran revisables todos los contratos y concesiones hechas por los Gobiernos anteriores desde el año de 1876, que hayan traído por consecuencia el acaparamiento de tierras, aguas y riquezas naturales de la Nación, por una sola persona o sociedad, y se faculta al Ejecutivo de la Unión para declararlos nulos cuando impliquen perjuicios graves para el interés público.

XIX. Con base en esta Constitución, el Estado dispondrá las medidas para la expedita y honesta impartición de la justicia agraria, con objeto de garantizar la seguridad jurídica en la tenencia de le (la, sic DOF 03-02-1983) tierra ejidal, comunal y de la pequeña propiedad, y apoyará la asesoría legal de los campesinos.

Son de jurisdicción federal todas las cuestiones que por límites de terrenos ejidales y comunales, cualquiera que sea el origen de éstos, se hallen pendientes o se susciten entre dos o más núcleos de población; así como las relacionadas con la tenencia de la tierra de los ejidos y comunidades. Para estos efectos y, en general, para la administración de justicia agraria, la ley instituirá tribunales dotados de autonomía y plena jurisdicción, integrados por magistrados propuestos por el Ejecutivo Federal y designados por la Cámara de Senadores o, en los recesos de ésta, por la Comisión Permanente.

La ley establecerá un órgano para la procuración de justicia agraria, y

XX. El Estado promoverá las condiciones para el desarrollo rural integral, con el propósito de generar empleo y garantizar a la población campesina el bienestar y su participación e incorporación en el desarrollo nacional, y fomentará la actividad agropecuaria y forestal para el óptimo uso de la tierra, con obras de infraestructura, insumos, créditos, servicios de capacitación y asistencia técnica. Asimismo expedirá la legislación reglamentaria para planear y organizar la producción agropecuaria, su industrialización y comercialización, considerándolas de interés público.

El desarrollo rural integral y sustentable a que se refiere el párrafo anterior, también tendrá entre sus fines que el Estado garantice el abasto suficiente y oportuno de los alimentos básicos que la ley establezca.

---

**Procedencia**

- Versión: DOF 15-10-2012 · CPEUM: reformas DOF 25-06-2012 a 15-10-2012 · commit [`9cdbce4`](https://github.com/BEG-lag/leyes-mx/commit/9cdbce4657f0fd3189d9b20e69314b6b7be67d0b)
- Decretos que recoge esa versión:
  - DOF 25-06-2012: DECRETO por el que se adiciona el párrafo segundo de la fracción XXI del artículo 73 de la Constitución Política de los Estados Unidos Mexicanos. ([PDF](https://www.diputados.gob.mx/LeyesBiblio/proceso/lxi/256_DOF_25jun12.pdf))
  - DOF 09-08-2012: DECRETO por el que se reforman y adicionan diversas disposiciones de la Constitución Política de los Estados Unidos Mexicanos, en materia política. ([PDF](https://www.diputados.gob.mx/LeyesBiblio/proceso/lxi/258_DOF_09ago12.pdf))
  - DOF 15-10-2012: DECRETO por el que se reforman los artículos 46, 76 y 105 de la Constitución Política de los Estados Unidos Mexicanos. ([PDF](https://www.diputados.gob.mx/LeyesBiblio/proceso/lxi/259_DOF_15oct12.pdf))
- El texto de este artículo no cambia desde la versión DOF 13-10-2011 ([`b6d33e0`](https://github.com/BEG-lag/leyes-mx/commit/b6d33e0468615bad79d0c51658d5273bede92e47)).
- En GitHub: [leyes/cpeum.md, líneas 529-639, commit 9cdbce4](https://github.com/BEG-lag/leyes-mx/blob/9cdbce4657f0fd3189d9b20e69314b6b7be67d0b/leyes/cpeum.md?plain=1#L529-L639)

**Advertencias**

- Entre el DOF 15-10-2012 y el 01-01-2013 se publicaron reformas sin versión propia en el archivo (DOF 30-11-2012: DECRETO por el que se reforma el Artículo 40 de la Constitución Política de los Estados Unidos Mexicanos.). Su texto aparece en la siguiente versión del archivo, DOF 26-02-2013; el texto mostrado NO las refleja.
- Esta versión agrupa 3 reformas publicadas entre el DOF 25-06-2012 y el 15-10-2012: no hay copia archivada intermedia, así que el commit lleva la fecha de la última.
- En la siguiente versión archivada (DOF 26-02-2013) este artículo no cambia: esas reformas no lo modificaron.

> La fecha de cada versión es la de su publicación en el DOF. La entrada en vigor la fijan los transitorios de cada decreto (herramienta `transitorios`).

_No oficial. Solo el DOF es fuente auténtica. No es asesoría legal. Textos: versiones consolidadas de la Cámara de Diputados vía [leyes-mx](https://github.com/BEG-lag/leyes-mx)._
````

## article_history

`{"law": "CPEUM", "article": "27"}` · 0.04 s · ok

````markdown
# CPEUM · historia del artículo 27

**Constitución Política de los Estados Unidos Mexicanos**

10 cambio(s) en 44 versiones archivadas de CPEUM (DOF 07-04-2006 a DOF 07-10-2026), de los cuales 2 parecen solo editoriales. Versiones sin cambios en este artículo: 33.

### DOF 07-04-2006 · presente en la versión más antigua del archivo · [`3c83f65`](https://github.com/BEG-lag/leyes-mx/commit/3c83f658ea1395e71a72475565c1a93314d8406e)

- Encabezado: Artículo 27.
- Nota del commit: Texto consolidado más antiguo disponible en el archivo; refleja todas las reformas publicadas hasta el DOF 07-04-2006.

### DOF 29-08-2008 · modificado: cambio menor sin nota de reforma (posible corrección editorial de la Cámara) · [`b2c41e3`](https://github.com/BEG-lag/leyes-mx/commit/b2c41e3814d434627d9a230e55ef62d287a67dc8)

- Encabezado: Artículo 27.
- Nota del commit: No hay una versión archivada entre estos decretos, así que este commit los agrupa.

### DOF 13-10-2011 · modificado · [`b6d33e0`](https://github.com/BEG-lag/leyes-mx/commit/b6d33e0468615bad79d0c51658d5273bede92e47)

- Encabezado: Artículo 27.
- Decretos de la versión:
  - DOF 12-10-2011: DECRETO por el que se adiciona un párrafo décimo al artículo 4o. y se reforma la fracción XXIX-J del artículo 73 de la Constitución Política de los Estados … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/proceso/lxi/142_DOF_12oct11.pdf))
  - DOF 12-10-2011: DECRETO por el que se reforman los párrafos sexto y séptimo del artículo 4o. y se adiciona la fracción XXIX-P al artículo 73, de la Constitución Política de … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/proceso/lxi/143_DOF_12oct11.pdf))
  - DOF 13-10-2011: DECRETO por el que se adiciona un párrafo tercero al artículo 4o. recorriéndose en el orden los subsecuentes y un segundo párrafo a la fracción XX del artículo … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/proceso/lxi/144_DOF_13oct11.pdf))
- Versión que agrupa varias reformas y la nota editorial no indica cuál tocó el artículo. Pista: el título del decreto del DOF 13-10-2011 menciona ese número de artículo.

### DOF 11-06-2013 · modificado · [`8f20cfc`](https://github.com/BEG-lag/leyes-mx/commit/8f20cfc728f94e59e96e2751a03bd8c20ec73d1b)

- Encabezado: Artículo 27.
- Decretos de la versión:
  - DOF 05-06-2013: DECRETO por el que se reforman los párrafos primero y último del artículo 25, así como el párrafo primero y tercero del apartado A del artículo 26 de la … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/proceso/cpeum/CPEUM_207_DOF_05jun13.pdf))
  - DOF 11-06-2013: DECRETO por el que se reforman y adicionan diversas disposiciones de los artículos 6o., 7o., 27, 28, 73, 78, 94 y 105 de la Constitución Política de los … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/ref/dof/CPEUM_ref_208_11jun13.pdf))
- Versión que agrupa varias reformas y la nota editorial no indica cuál tocó el artículo. Pista: el título del decreto del DOF 11-06-2013 menciona ese número de artículo.

### DOF 10-02-2014 · modificado · [`faadb30`](https://github.com/BEG-lag/leyes-mx/commit/faadb30067a819a363db64453e510d540ef415c3)

- Encabezado: Artículo 27.
- Decreto (según la nota editorial del artículo):
  - DOF 20-12-2013: DECRETO por el que se reforman y adicionan diversas disposiciones de la Constitución Política de los Estados Unidos Mexicanos, en Materia de Energía. ([PDF](https://www.diputados.gob.mx/LeyesBiblio/proceso/docleg/62/212_DOF_20dic13.pdf))
- La versión agrupa además 7 decreto(s) de otras fechas que no citan este artículo en sus notas.

### DOF 29-01-2016 · modificado · [`40fbbef`](https://github.com/BEG-lag/leyes-mx/commit/40fbbefd6cafc18aab1f77b34b65486f5b2201e3)

- Encabezado: Artículo 27.
- Decreto (según la nota editorial del artículo):
  - DOF 29-01-2016: DECRETO por el que se declaran reformadas y derogadas diversas disposiciones de la Constitución Política de los Estados Unidos Mexicanos, en materia de la … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/proceso/docleg/63/227_DOF_29ene16.pdf))
- La versión agrupa además 6 decreto(s) de otras fechas que no citan este artículo en sus notas.

### DOF 11-03-2021 · modificado: solo cambian las notas editoriales de la Cámara · [`76d8e18`](https://github.com/BEG-lag/leyes-mx/commit/76d8e18998eb891ad3a9e145f1528327ebcb8757)

- Encabezado: Artículo 27.
- Nota del commit: No hay una versión archivada entre estos decretos, así que este commit los agrupa.

### DOF 15-11-2024 · modificado · [`f7d255b`](https://github.com/BEG-lag/leyes-mx/commit/f7d255b34b363c2de4851aba0334f3fbf8a87ce7)

- Encabezado: Artículo 27.
- Decreto (según la nota editorial del artículo):
  - DOF 31-10-2024: DECRETO por el que se reforman el párrafo quinto del artículo 25, los párrafos sexto y séptimo del artículo 27 y el párrafo cuarto del artículo 28 de la … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/ref/dof/CPEUM_ref_262_31oct24.pdf))
  - DOF 31-10-2024: DECRETO por el que se reforma el primer párrafo de la fracción II del artículo 107, y se adiciona un quinto párrafo al artículo 105, de la Constitución … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/ref/dof/CPEUM_ref_263_31oct24.pdf))
- La versión agrupa además 2 decreto(s) de otras fechas que no citan este artículo en sus notas.

### DOF 02-12-2024 · modificado · [`b5be146`](https://github.com/BEG-lag/leyes-mx/commit/b5be146efb0eca84194be902b21efc6e2500839d)

- Encabezado: Artículo 27.
- Decreto (según la nota editorial del artículo):
  - DOF 02-12-2024: DECRETO por el que se reforman y adicionan los artículos 4o. y 27 de la Constitución Política de los Estados Unidos Mexicanos, en materia de bienestar. ([PDF](https://www.diputados.gob.mx/LeyesBiblio/ref/dof/CPEUM_ref_265_02dic24.pdf))
  - DOF 02-12-2024: DECRETO por el que se reforma y adiciona la fracción XII del Apartado A del artículo 123 de la Constitución Política de los Estados Unidos Mexicanos, en … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/ref/dof/CPEUM_ref_266_02dic24.pdf))
  - DOF 02-12-2024: DECRETO por el que se reforman y adicionan los artículos 3o., 4o. y 73 de la Constitución Política de los Estados Unidos Mexicanos, en materia de protección y … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/ref/dof/CPEUM_ref_267_02dic24.pdf))

### DOF 17-01-2025 · modificado · [`b237612`](https://github.com/BEG-lag/leyes-mx/commit/b23761265e286e20309461ddf09fb65268837b36)

- Encabezado: Artículo 27.
- Decreto (según la nota editorial del artículo):
  - DOF 20-12-2024: DECRETO por el que se reforman, adicionan y derogan diversas disposiciones de la Constitución Política de los Estados Unidos Mexicanos, en materia de … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/ref/dof/CPEUM_ref_268_20dic24.pdf))
- La versión agrupa además 3 decreto(s) de otras fechas que no citan este artículo en sus notas.

### DOF 01-04-2025 · modificado · [`b18e57f`](https://github.com/BEG-lag/leyes-mx/commit/b18e57fd7a46fef9b25743876b27609fdb4c05b4)

- Encabezado: Artículo 27.
- Decreto (según la nota editorial del artículo):
  - DOF 17-03-2025: DECRETO por el que se reforman y adicionan diversas disposiciones de los artículos 4o. y 27 de la Constitución Política de los Estados Unidos Mexicanos, en … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/ref/dof/CPEUM_ref_272_17mar25.pdf))
- La versión agrupa además 3 decreto(s) de otras fechas que no citan este artículo en sus notas.

**Notas**

- El historial empieza en la versión más antigua archivada; cuando varias reformas caen entre dos copias archivadas, un solo commit las agrupa con la fecha de la última. La nota editorial de la Cámara («Artículo reformado DOF ...») indica cuál de ellas tocó el artículo.

> La fecha de cada versión es la de su publicación en el DOF. La entrada en vigor la fijan los transitorios de cada decreto (herramienta `transitorios`).

_No oficial. Solo el DOF es fuente auténtica. No es asesoría legal. Textos: versiones consolidadas de la Cámara de Diputados vía [leyes-mx](https://github.com/BEG-lag/leyes-mx)._
````

## diff_article

`{"law": "CPEUM", "article": "27", "date_from": "2013-01-01"}` · 0.15 s · ok

````markdown
# CPEUM · Artículo 27. · DOF 15-10-2012 → DOF 07-10-2026

Comparación entre el texto aplicable al 01-01-2013 (versión DOF 15-10-2012, [`9cdbce4`](https://github.com/BEG-lag/leyes-mx/commit/9cdbce4657f0fd3189d9b20e69314b6b7be67d0b)) y al 17-11-2026 (versión DOF 07-10-2026, [`6cd26a9`](https://github.com/BEG-lag/leyes-mx/commit/6cd26a99e6bfbb14d8520164efafd1c181ea4b24)).

**Versiones que cambiaron el artículo en ese lapso**

- DOF 11-06-2013 · modificado · CPEUM: reformas DOF 05-06-2013 a 11-06-2013
- DOF 10-02-2014 · modificado · nota editorial: DOF 20-12-2013
- DOF 29-01-2016 · modificado · nota editorial: DOF 29-01-2016
- DOF 11-03-2021 · modificado · CPEUM: reformas DOF 08-05-2020 a 11-03-2021
- DOF 15-11-2024 · modificado · nota editorial: DOF 31-10-2024
- DOF 02-12-2024 · modificado · nota editorial: DOF 02-12-2024
- DOF 17-01-2025 · modificado · nota editorial: DOF 20-12-2024
- DOF 01-04-2025 · modificado · nota editorial: DOF 17-03-2025

Leyenda: `[-texto eliminado-]` · `{+texto añadido+}`

… (3 párrafos sin cambios)

{+*Párrafo reformado DOF 06-02-1976, 10-08-1987, 06-01-1992*+}

… (1 párrafo sin cambios)

{+*Párrafo reformado DOF 20-01-1960*+}

Son propiedad de la Nación las aguas de los mares territoriales en la extensión y términos que fije [-(-]el[-, sic DOF 20-01-1960)-] Derecho Internacional; las aguas marinas interiores; las de las lagunas y esteros que se comuniquen permanente o intermitentemente con el mar; las de los lagos interiores de formación natural que estén ligados directamente a corrientes constantes; las de los ríos y sus afluentes directos o indirectos, desde el punto del cauce en que se inicien las primeras aguas permanentes, intermitentes o torrenciales, hasta su desembocadura en el mar, lagos, lagunas o esteros de propiedad nacional; las de las corrientes constantes o [-interminentes (-]intermitentes[-, sic DOF 20-01-1960)-] y sus afluentes directos o indirectos, cuando el cauce de aquéllas en toda su extensión o en parte de ellas, sirva de límite al territorio nacional o a dos entidades federativas, o cuando pase de una entidad federativa a otra o cruce la línea divisoria de la República; la de los lagos, lagunas o esteros cuyos vasos, zonas o riberas, estén cruzadas por líneas divisorias de dos o más entidades o entre la República y un país vecino, o cuando el límite de las riberas sirva de lindero entre dos entidades federativas o a la República con un país vecino; las de los manantiales que broten en las playas, zonas marítimas, cauces, vasos o riberas de los lagos, lagunas o esteros de propiedad nacional, y las que se extraigan de las minas; y los cauces, lechos o riberas de los lagos y corrientes interiores en la extensión que fija la ley. Las aguas del subsuelo pueden ser libremente alumbradas mediante obras artificiales y apropiarse por el dueño del terreno, pero cuando lo exija el interés público o se afecten otros aprovechamientos[-;-] {+,+} el Ejecutivo Federal podrá reglamentar su extracción y utilización y aún establecer zonas vedadas, al igual que para las demás aguas de propiedad nacional. Cualesquiera otras aguas no incluidas en la enumeración anterior, se considerarán como parte integrante de la propiedad de los terrenos por los que corran o en los que se encuentren sus depósitos, pero si se localizaren en dos o más predios, el aprovechamiento de estas aguas se considerará de utilidad pública, y quedará sujeto a las disposiciones que dicten [-los Estados-] {+las entidades federativas+}.

{+*Párrafo reformado DOF 21-04-1945, 20-01-1960, 29-01-2016*+}

En los casos a que se refieren los dos párrafos anteriores, el dominio de la Nación es inalienable e imprescriptible y la explotación, el uso o el aprovechamiento de los recursos de que se trata, por los particulares o por sociedades constituidas conforme a las leyes mexicanas, no podrá realizarse sino mediante concesiones, otorgadas por el Ejecutivo Federal, de acuerdo con las reglas y condiciones que establezcan las leyes. Las normas legales relativas a obras o trabajos de explotación de los minerales y substancias a que se refiere el párrafo cuarto, regularán la ejecución y comprobación de los que se efectúen o deban efectuarse a partir de su vigencia, independientemente de la fecha de otorgamiento de las concesiones, y su inobservancia dará lugar a la cancelación de éstas. El Gobierno Federal tiene la facultad de establecer reservas nacionales y suprimirlas. Las declaratorias correspondientes se harán por el Ejecutivo en los casos y condiciones que las leyes prevean. Tratándose [-del petróleo y de los carburos de hidrógeno sólidos, líquidos o gaseosos o-] de minerales [-radioactivos,-] {+radiactivos y litio+} no se otorgarán concesiones [-ni contratos, ni subsistirán los que en su caso se hayan otorgado y la Nación llevará a cabo la explotación de esos productos, en los términos que señale la Ley Reglamentaria respectiva-]. Corresponde exclusivamente a la Nación [-generar, conducir, transformar, distribuir-] {+la planeación+} y [-abastecer-] {+el control del sistema eléctrico nacional en los términos del artículo 28 de esta Constitución, así como el servicio público de transmisión y distribución de+} energía eléctrica [-que tenga por objeto la prestación de servicio público. En esta materia-] {+; en estas actividades+} no se otorgarán concesiones [-a-] {+. Las leyes determinarán la forma en que+} los particulares [-y-] {+podrán participar en las demás actividades de+} la [-Nación aprovechará los bienes-] {+industria eléctrica, que en ningún caso tendrán prevalencia sobre la empresa pública del Estado, cuya esencia es cumplir con su responsabilidad social+} y [-recursos naturales que se requieran para dichos fines-] {+garantizar la continuidad y accesibilidad del servicio público de electricidad+}.

{+*Párrafo reformado DOF 09-11-1940, 20-01-1960, 06-02-1975, 11-06-2013, 20-12-2013, 31-10-2024, 20-12-2024*+}

{+Tratándose del petróleo y de los hidrocarburos sólidos, líquidos o gaseosos, en el subsuelo, la propiedad de la Nación es inalienable e imprescriptible y no se otorgarán concesiones. Con el propósito de obtener ingresos para el Estado que contribuyan al desarrollo de largo plazo de la Nación, ésta llevará a cabo las actividades de exploración y extracción del petróleo y demás hidrocarburos mediante asignaciones a empresas públicas del Estado o a través de contratos con éstas o con particulares, en los términos de la Ley Reglamentaria. Para cumplir con el objeto de dichas asignaciones o contratos las empresas públicas del Estado podrán contratar con particulares. En cualquier caso, los hidrocarburos en el subsuelo son propiedad de la Nación y así deberá afirmarse en las asignaciones o contratos.+}

{+*Párrafo adicionado DOF 20-12-2013. Reformado DOF 31-10-2024*+}

… (1 párrafo sin cambios)

{+*Párrafo adicionado DOF 29-12-1960. Fe de erratas al párrafo DOF 07-01-1961. Reformado DOF 06-02-1975*+}

… (1 párrafo sin cambios)

{+*Párrafo adicionado DOF 06-02-1976*+}

… (1 párrafo sin cambios)

{+*Párrafo reformado DOF 02-12-1948, 20-01-1960*+}

… (2 párrafos sin cambios)

{+*Fracción reformada DOF 02-12-1948, 20-01-1960*+}

… (1 párrafo sin cambios)

{+*Fracción reformada DOF 28-01-1992*+}

… (1 párrafo sin cambios)

{+*Fracción reformada DOF 28-01-1992*+}

… (3 párrafos sin cambios)

{+*Fracción reformada DOF 06-01-1992*+}

… (1 párrafo sin cambios)

VI. [-Los estados y el Distrito Federal-] {+Las entidades federativas+}, lo mismo que los [-municipios-] {+Municipios+} de toda la República, tendrán plena capacidad para adquirir y poseer todos los bienes raíces necesarios para los servicios públicos.

{+*Párrafo reformado DOF 08-10-1974, 06-01-1992, 29-01-2016*+}

Las leyes de la Federación y de [-los Estados-] {+las entidades federativas+} en sus respectivas jurisdicciones, determinarán los casos en que sea de utilidad pública la ocupación de la propiedad privada, y de acuerdo con dichas leyes la autoridad administrativa hará la declaración correspondiente. El precio que se fijará como indemnización a la cosa expropiada, se basará en la cantidad que como valor fiscal de ella figure en las oficinas catastrales o recaudadoras, ya sea que este valor haya sido manifestado por el propietario o simplemente aceptado por él de un modo tácito por haber pagado sus contribuciones con esta base. El exceso de valor o el demérito que haya tenido la propiedad particular por las mejoras o deterioros ocurridos con posterioridad a la fecha de la asignación del valor fiscal, será lo único que deberá quedar sujeto a juicio pericial y a resolución judicial. Esto mismo se observará cuando se trate de objetos cuyo valor no esté fijado en las oficinas rentísticas.

{+*Párrafo reformado DOF 29-01-2016*+}

… (8 párrafos sin cambios)

{+*Fracción reformada DOF 06-12-1937, 06-01-1992*+}

… (7 párrafos sin cambios)

{+*Fe de erratas a la fracción DOF 03-03-1934. Reformada DOF 12-02-1947. Derogada DOF 06-01-1992*+}

… (1 párrafo sin cambios)

{+*Fracción reformada DOF 08-10-1974. Derogada DOF 06-01-1992*+}

… (1 párrafo sin cambios)

{+*Fracción reformada DOF 08-10-1974. Derogada DOF 06-01-1992*+}

… (1 párrafo sin cambios)

{+*Fracción derogada DOF 06-01-1992*+}

… (1 párrafo sin cambios)

{+*Fracción reformada DOF 12-02-1947. Derogada DOF 06-01-1992*+}

… (7 párrafos sin cambios)

{+*Fracción reformada DOF 12-02-1947, 06-01-1992*+}

… (1 párrafo sin cambios)

{+*Fracción derogada DOF 06-01-1992*+}

… (3 párrafos sin cambios)

{+*Fracción reformada DOF 08-10-1974, 06-01-1992*+}

… (1 párrafo sin cambios)

XIX. Con base en esta Constitución, el Estado dispondrá las medidas para la expedita y honesta impartición de la justicia agraria, con objeto de garantizar la seguridad jurídica en la tenencia de le ([-la,-] sic DOF 03-02-1983) tierra ejidal, comunal y de la pequeña propiedad, y apoyará la asesoría legal de los campesinos.

… (1 párrafo sin cambios)

{+*Párrafo adicionado DOF 06-01-1992*+}

… (1 párrafo sin cambios)

{+*Párrafo adicionado DOF 06-01-1992*+}

{+*Fracción adicionada DOF 03-02-1983*+}

XX. El Estado promoverá las condiciones para el desarrollo rural [-integral-] {+, cultural, económico y de salud+}, con el propósito de generar empleo y garantizar a la población campesina [-el-] {+su+} bienestar y su participación e incorporación en el desarrollo nacional, [-y-] fomentará la actividad agropecuaria y forestal{+, cultivos tradicionales con semillas nativas, en especial el sistema milpa,+} para el óptimo uso de la tierra {+libre de cultivos de maíz genéticamente modificado, en los términos definidos en el artículo 4o.+}, con obras de infraestructura, insumos, créditos, servicios de capacitación{+, investigación, innovación, conservación de la agrobiodiversidad+} y asistencia técnica{+, fortaleciendo las instituciones públicas nacionales+}. Asimismo{+,+} expedirá la legislación reglamentaria para planear{+, organizar+} y [-organizar-] {+monitorear+} la producción agropecuaria, su industrialización y comercialización, considerándolas de interés público.

{+*Párrafo reformado DOF 17-03-2025*+}

… (1 párrafo sin cambios)

{+*Párrafo adicionado DOF 13-10-2011*+}

{+El Estado garantizará, en los términos que fije la ley, la entrega de:+}

{+a) Un jornal seguro, justo y permanente a campesinos que cultiven sus tierras con árboles frutales, maderables y especies que requieren ser procesadas;+}

{+b) Un apoyo anual directo y fertilizantes gratuitos a productores de pequeña escala, y+}

{+c) Un apoyo anual directo a pescadores de pequeña escala.+}

{+*Párrafo con incisos adicionado DOF 02-12-2024*+}

{+El Estado mantendrá precios de garantía para el maíz, frijol, leche, arroz y trigo harinero o panificable, en los términos de las disposiciones aplicables.+}

{+*Párrafo adicionado DOF 02-12-2024*+}

{+*Fracción adicionada DOF 03-02-1983*+}

{+*Artículo reformado DOF 10-01-1934*+}

- Antes: [leyes/cpeum.md en 9cdbce4](https://github.com/BEG-lag/leyes-mx/blob/9cdbce4657f0fd3189d9b20e69314b6b7be67d0b/leyes/cpeum.md?plain=1#L529-L639)
- Después: [leyes/cpeum.md en 6cd26a9](https://github.com/BEG-lag/leyes-mx/blob/6cd26a99e6bfbb14d8520164efafd1c181ea4b24/leyes/cpeum.md?plain=1#L1114-L1300)

**Advertencias**

- Entre el DOF 15-10-2012 y el 01-01-2013 se publicaron reformas sin versión propia en el archivo (DOF 30-11-2012: DECRETO por el que se reforma el Artículo 40 de la Constitución Política de los Estados Unidos Mexicanos.). Su texto aparece en la siguiente versión del archivo, DOF 26-02-2013; el texto mostrado NO las refleja.
- Esta versión agrupa 3 reformas publicadas entre el DOF 25-06-2012 y el 15-10-2012: no hay copia archivada intermedia, así que el commit lleva la fecha de la última.

> La fecha de cada versión es la de su publicación en el DOF. La entrada en vigor la fijan los transitorios de cada decreto (herramienta `transitorios`).

_No oficial. Solo el DOF es fuente auténtica. No es asesoría legal. Textos: versiones consolidadas de la Cámara de Diputados vía [leyes-mx](https://github.com/BEG-lag/leyes-mx)._
````

## diff_reform

`{"law": "LFT", "reform_date": "2019-05-01", "limit": 3}` · 0.03 s · ok

````markdown
# LFT · reforma DOF 01-05-2019

**Ley Federal del Trabajo**

Decreto(s) publicado(s) ese día:

- DECRETO por el que se reforman, adicionan y derogan diversas disposiciones de la Ley Federal del Trabajo, de la Ley Orgánica del Poder Judicial de la Federación, de la Ley Federal de la Defensoría Pública, de la Ley del … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_ref30_01may19.pdf))

Comparación: versión DOF 22-06-2018 ([`2ed3ea7`](https://github.com/BEG-lag/leyes-mx/commit/2ed3ea76ea8f4392c157407ddd139a6c93fe591e)) → versión DOF 02-07-2019 ([`8157e28`](https://github.com/BEG-lag/leyes-mx/commit/8157e2821aba6a04c1e889a8d38f38848c3ec2f0)).

**Resumen**

- 475 artículo(s) modificado(s), 96 añadido(s), 0 que ya no aparece(n).
- De ellos, 559 tienen una nota editorial que cita el DOF 01-05-2019.
- Transitorios nuevos de 3 decreto(s) (DOF 01-05-2019, 04-06-2019, 02-07-2019): consúltalos con `transitorios`.
- Encabezados nuevos: CAPITULO XIII · Personas Trabajadoras del Hogar; CAPITULO IX BIS · Del Centro Federal de Conciliación y Registro Laboral; CAPITULO IX TER · De los Centros de Conciliación de las Entidades Federativas y …; CAPITULO XII · De la Competencia de los Tribunales; CAPITULO I · De los procedimientos de designación de representantes de los …; CAPITULO I · Del Procedimiento de Conciliación Prejudicial; CAPITULO II · De los Conciliadores; CAPITULO III · Del Procedimiento para la Selección de Conciliadores
- Encabezados que ya no aparecen: CAPITULO XIII · Trabajadores domésticos; CAPITULO XII · Junta federal de conciliación y arbitraje; CAPITULO I · Representantes de los trabajadores y de los patrones en las juntas …; CAPITULO V · De la Actuación de las Juntas; CAPITULO XVII · Procedimiento Ordinario Ante las Juntas de Conciliación y …; CAPITULO XVIII · De los Procedimientos Especiales

**Con nota que cita el DOF 01-05-2019 (559):** 3o., 3o. Ter. (añadido), 4o., 5o., 22., 25., 28., 33., 42., 47., 48., 48 Bis. (añadido), 49., 57., 75., 101., 110., 114., 121., 127., 132., 133., 146., 152., 153., 153-K., 153-L., 153-N., 153-Q., 153-X., 157., 158., 163., 164., 176., 183., 207., 210., 211., 245., 245 Bis. (añadido), 273., 277., 278., 279 Quáter. (añadido), 280 Bis. (añadido), 283., 331., 332., 333., 334., 336., 337., 338., 340., 342., 343-E., 353-O., 353-R., 353-S., 353-T., 357., 357 Bis. (añadido), 358., 360., 364., 364 Bis., 365., 365 Bis., 366., 367., 368., 369., 371., 371 Bis. (añadido), 373., 374., 376., 377., 378., 384., 386 Bis. (añadido), 387., 388., 389., 390., 390 Bis. (añadido), 390 Ter. (añadido), 391., 391 Bis., 392., 395., 399., 399 Bis., 399 Ter. (añadido), 400 Bis. (añadido), 401., 407., 408., 409., 411., 412., 414., 415., 416., 418., 419., 419 Bis., 421., 424., 424 Bis., 426., 429., 430., 431., 432., 435., 439., 448., 449., 451., 459., 469., 476., 483., 490., 493., 501., 503., 504., 505., 512-B., 512-C., 513., 514., 518., 519., 521., 523., 525 Bis., 527., 530., 530 Bis., 531., 539-B., 541., 549., 590-A. (añadido), 590-B. (añadido), 590-C. (añadido), 590-D. (añadido), 590-E. (añadido), 590-F. (añadido), 604., 605., 605 Bis., 606., 607., 608., 609., 610., 611., 612., 613., 614., 615., 616., 617., 618., 619., 620., 621., 622., 623., 624., 625., 626., 627., 627-A., 627-B., 627-C., 628., 629., 630., 631., 632., 633., 634., 635., 636., 637., 638., 639., 640., 641., 642., 643., 644., 645., 646. y 359 más

**Sin esa nota (12; otras reformas de la versión o cambios editoriales):** 170 Bis. (añadido), 331 Bis. (añadido), 331 Ter. (añadido), 334 Bis. (añadido), 335., 336 Bis. (añadido), 337 Bis. (añadido), 339., 341., 343., 542., 641-A.

Leyenda: `[-texto eliminado-]` · `{+texto añadido+}`

## Artículo 3o. (modificado; nota cita DOF 01-05-2019)

[-El trabajo es un derecho y un deber sociales. No es artículo de comercio.-]

{+El trabajo es un derecho y un deber social. No es artículo de comercio, y exige respeto para las libertades y dignidad de quien lo presta, así como el reconocimiento a las diferencias entre hombres y mujeres para obtener su igualdad ante la ley. Debe efectuarse en condiciones que aseguren la vida digna y la salud para las y los trabajadores y sus familiares dependientes.+}

{+*Párrafo reformado DOF 01-05-2019*+}

… (2 párrafos sin cambios)

Es de interés social {+garantizar un ambiente laboral libre de discriminación y de violencia,+} promover y vigilar la capacitación, el adiestramiento, la formación para y en el trabajo, la certificación de competencias laborales, la productividad y la calidad en el trabajo, la sustentabilidad ambiental, así como los beneficios que éstas deban generar tanto a los trabajadores como a los patrones.

{+*Párrafo reformado DOF 01-05-2019*+}

… (1 párrafo sin cambios)

## Artículo 3o. Ter. (añadido; nota cita DOF 01-05-2019)

{+Para efectos de esta Ley se entenderá por:

I. Autoridad Conciliadora: El Centro Federal de Conciliación y Registro Laboral o los Centros de Conciliación de las entidades federativas, según corresponda;

II. Autoridad Registral: El Centro Federal de Conciliación y Registro Laboral;

III. Centros de Conciliación: Los Centros de conciliación de las entidades federativas o el Centro Federal de Conciliación y Registro Laboral, según corresponda;

IV. Constitución: La Constitución Política de los Estados Unidos Mexicanos;

V. Día: Se hace referencia a día hábil, salvo que expresamente se mencione que se trata de días naturales;

VI. Tribunal: El juez laboral, y

VII. Correr traslado: poner a disposición de alguna de las partes algún documento o documentos en el local del Tribunal, salvo los casos previstos en esta Ley.

*Artículo adicionado DOF 01-05-2019*+}

## Artículo 4o. (modificado; nota cita DOF 01-05-2019)

… (2 párrafos sin cambios)

a) Cuando se trate de sustituir o se sustituya definitivamente a un trabajador que reclame la reinstalación en su empleo sin haberse resuelto el caso por [-la Junta de Conciliación y Arbitraje-] {+el Tribunal+}.

*Inciso reformado DOF 30-11-2012{+, 01-05-2019+}*

… (4 párrafos sin cambios)

Mostrando artículos 1-3 de 571. Usa offset=3 para continuar, o diff_article para uno en particular.

**Advertencias**

- No hay copia archivada justo después del DOF 01-05-2019: esta comparación es entre las versiones DOF 22-06-2018 y DOF 02-07-2019, así que incluye cambios de todas las reformas publicadas en ese lapso. Los otros decretos de esa versión son del DOF 04-06-2019, 02-07-2019. Los artículos cuya nota editorial cita el DOF 01-05-2019 se listan primero; los demás pueden venir de otra reforma.

> La fecha de cada versión es la de su publicación en el DOF. La entrada en vigor la fijan los transitorios de cada decreto (herramienta `transitorios`).

_No oficial. Solo el DOF es fuente auténtica. No es asesoría legal. Textos: versiones consolidadas de la Cámara de Diputados vía [leyes-mx](https://github.com/BEG-lag/leyes-mx)._
````

## diff_article

`{"law": "LFT", "article": "371", "date_from": "2019-01-01", "date_to": "2019-12-31"}` · 0.02 s · ok

````markdown
# LFT · Artículo 371. · DOF 22-06-2018 → DOF 02-07-2019

Comparación entre el texto aplicable al 01-01-2019 (versión DOF 22-06-2018, [`2ed3ea7`](https://github.com/BEG-lag/leyes-mx/commit/2ed3ea76ea8f4392c157407ddd139a6c93fe591e)) y al 31-12-2019 (versión DOF 02-07-2019, [`8157e28`](https://github.com/BEG-lag/leyes-mx/commit/8157e2821aba6a04c1e889a8d38f38848c3ec2f0)).

**Versiones que cambiaron el artículo en ese lapso**

- DOF 02-07-2019 · modificado · nota editorial: DOF 01-05-2019

Leyenda: `[-texto eliminado-]` · `{+texto añadido+}`

… (18 párrafos sin cambios)

IX. Procedimiento para la elección de la directiva {+sindical+} y [-número de miembros-] {+secciones sindicales+}, [-salvaguardando-] el [-libre-] {+cual se llevará a cabo mediante el+} ejercicio del voto [-con las modalidades que acuerde la asamblea general; de votación indirecta-] {+directo, personal, libre, directo+} y [-secreta o votación directa y secreta;-] {+secreto.+}

{+Para tal efecto, los estatutos deberán observar las normas siguientes:+}

{+a) La convocatoria de elección se emitirá con firma autógrafa de las personas facultadas para ello, debiendo precisar fecha, hora, lugar del proceso y demás requisitos estatutariamente exigidos;+}

{+b) La convocatoria deberá publicarse en el local sindical y en los lugares de mayor afluencia de los miembros en el centro de trabajo, con una anticipación mínima de diez días;+}

{+c) El lugar que se determine para la celebración del proceso electoral, así como la documentación y materiales que se elaboren para la realización, deberán garantizar que la votación se desarrolle de forma segura, directa, personal, libre y secreta;+}

{+d) Se integrará un padrón completo y actualizado de los miembros del sindicato con derecho a votar, que deberá publicarse y darse a conocer entre éstos con al menos tres días de antelación a la elección;+}

{+e) Establecer un procedimiento que asegure la identificación de los afiliados que tengan derecho a votar, y+}

{+f) La documentación, material y boletas para la elección de integración de los órganos internos de los sindicatos a que se refiere este inciso, contendrá cuando menos los siguientes datos y requisitos:+}

{+1.- Municipio y entidad federativa en que se realice la votación;+}

{+2.- Cargo para el que se postula al candidato o candidatos;+}

{+3.- Emblema y color de cada una de las planillas que participan con candidatos en la elección de que se trate;+}

{+4.- El nombre completo del candidato o candidatos a elegir, y+}

{+5.- Las boletas deberán validarse en el reverso con las firmas de por lo menos dos integrantes de la Comisión Electoral que para tales efectos acuerde el sindicato.+}

{+El procedimiento de elección que realicen los miembros de un sindicato respecto al Secretario General o su equivalente a nivel nacional, estatal, seccional, local o municipal, se realizará de manera independiente de la elección de delegados a los congresos o convenciones sindicales, cumpliendo con los requisitos a que se refiere este inciso.+}

{+En virtud de que estos requisitos son esenciales para expresar la libre voluntad de los afiliados al sindicato, de incumplirse éstos, el procedimiento de elección carecerá de validez, ya sea a nivel general o seccional, según sea el caso;+}

{+*Fracción reformada DOF 30-11-2012, 01-05-2019*+}

{+IX Bis. En la integración de las directivas sindicales se establecerá la representación proporcional en razón de género;+}

{+*Fracción adicionada DOF 01-05-2019*+}

{+IX Ter. Normas para la integración y funcionamiento de una instancia de decisión colegiada, que será responsable de organizar y calificar los procedimientos de elección de los órganos internos del sindicato;+}

{+*Fracción adicionada DOF 01-05-2019*+}

{+X. Período de duración de la directiva sindical y de las representaciones seccionales. En el caso de reelección, será facultad de la asamblea decidir mediante voto personal, libre, directo y secreto el período de duración y el número de veces que pueden reelegirse los dirigentes sindicales. El período de duración de la directiva y en su caso la reelección, deberán respetar las garantías a que se refiere el artículo 358, fracción II, de esta Ley;+}

*Fracción reformada DOF [-30-11-2012-] {+01-05-2019+}*

[-X. Período de duración de la directiva;-]

… (2 párrafos sin cambios)

XIII. Época {+y forma+} de presentación de [-cuentas-] {+la cuenta completa y detallada de la administración del patrimonio sindical+} y sanciones a sus directivos en caso de incumplimiento.

{+*Párrafo reformado DOF 01-05-2019*+}

… (3 párrafos sin cambios)

{+XIV Bis. Procedimiento para llevar a cabo la consulta a los trabajadores mediante voto personal, libre y secreto para la aprobación del contenido de contratos colectivos de trabajo iniciales y de sus revisiones. Para tal efecto, los estatutos deberán observar el procedimiento contemplado en el artículo 390 Ter, fracción II de la presente Ley, y+}

{+*Fracción adicionada DOF 01-05-2019*+}

… (1 párrafo sin cambios)

- Antes: [leyes/lft.md en 2ed3ea7](https://github.com/BEG-lag/leyes-mx/blob/2ed3ea76ea8f4392c157407ddd139a6c93fe591e/leyes/lft.md?plain=1#L3999-L4055)
- Después: [leyes/lft.md en 8157e28](https://github.com/BEG-lag/leyes-mx/blob/8157e2821aba6a04c1e889a8d38f38848c3ec2f0/leyes/lft.md?plain=1#L4505-L4605)

**Advertencias**

- Esta versión agrupa 2 reformas publicadas entre el DOF 30-05-2018 y el 22-06-2018: no hay copia archivada intermedia, así que el commit lleva la fecha de la última.
- Esta versión agrupa 3 reformas publicadas entre el DOF 01-05-2019 y el 02-07-2019: no hay copia archivada intermedia, así que el commit lleva la fecha de la última.

> La fecha de cada versión es la de su publicación en el DOF. La entrada en vigor la fijan los transitorios de cada decreto (herramienta `transitorios`).

_No oficial. Solo el DOF es fuente auténtica. No es asesoría legal. Textos: versiones consolidadas de la Cámara de Diputados vía [leyes-mx](https://github.com/BEG-lag/leyes-mx)._
````

## get_article

`{"law": "LFT", "article": "371", "date": "2019-06-01"}` · 0.00 s · ok

````markdown
# LFT · Artículo 371.

**Ley Federal del Trabajo** › TITULO SEPTIMO · Relaciones Colectivas de Trabajo › CAPITULO II · Sindicatos, federaciones y confederaciones

Texto aplicable al 01-06-2019: versión DOF 22-06-2018 (commit [`2ed3ea7`](https://github.com/BEG-lag/leyes-mx/commit/2ed3ea76ea8f4392c157407ddd139a6c93fe591e)).

---

Los estatutos de los sindicatos contendrán:

I. Denominación que le distinga de los demás;

II. Domicilio;

III. Objeto;

IV. Duración. Faltando esta disposición se entenderá constituido el sindicato por tiempo indeterminado;

V. Condiciones de admisión de miembros;

VI. Obligaciones y derechos de los asociados;

VII. Motivos y procedimientos de expulsión y correcciones disciplinarias. En los casos de expulsión se observarán las normas siguientes:

a) La asamblea de trabajadores se reunirá para el solo efecto de conocer de la expulsión.

b) Cuando se trate de sindicatos integrados por secciones, el procedimiento de expulsión se llevará a cabo ante la asamblea de la sección correspondiente, pero el acuerdo de expulsión deberá someterse a la decisión de los trabajadores de cada una de las secciones que integren el sindicato.

c) El trabajador afectado será oído en defensa, de conformidad con las disposiciones contenidas en los estatutos.

d) La asamblea conocerá de las pruebas que sirvan de base al procedimiento y de las que ofrezca el afectado.

e) Los trabajadores no podrán hacerse representar ni emitir su voto por escrito.

f) La expulsión deberá ser aprobada por mayoría de las dos terceras partes del total de los miembros del sindicato.

g) La expulsión sólo podrá decretarse por los casos expresamente consignados en los estatutos, debidamente comprobados y exactamente aplicables al caso;

VIII. Forma de convocar a asamblea, época de celebración de las ordinarias y quórum requerido para sesionar. En el caso de que la directiva no convoque oportunamente a las asambleas previstas en los estatutos, los trabajadores que representen el treinta y tres por ciento del total de los miembros del sindicato o de la sección, por lo menos, podrán solicitar de la directiva que convoque a la asamblea, y si no lo hace dentro de un término de diez días, podrán los solicitantes hacer la convocatoria, en cuyo caso, para que la asamblea pueda sesionar y adoptar resoluciones, se requiere que concurran las dos terceras partes del total de los miembros del sindicato o de la sección.

Las resoluciones deberán adoptarse por el cincuenta y uno por ciento del total de los miembros del sindicato o de la sección, por lo menos;

*Fe de erratas al párrafo DOF 30-04-1970*

IX. Procedimiento para la elección de la directiva y número de miembros, salvaguardando el libre ejercicio del voto con las modalidades que acuerde la asamblea general; de votación indirecta y secreta o votación directa y secreta;

*Fracción reformada DOF 30-11-2012*

X. Período de duración de la directiva;

XI. Normas para la administración, adquisición y disposición de los bienes, patrimonio del sindicato;

XII. Forma de pago y monto de las cuotas sindicales;

XIII. Época de presentación de cuentas y sanciones a sus directivos en caso de incumplimiento.

Para tales efectos, se deberán establecer instancias y procedimientos internos que aseguren la resolución de controversias entre los agremiados, con motivo de la gestión de los fondos sindicales.

*Fracción reformada DOF 30-11-2012*

XIV. Normas para la liquidación del patrimonio sindical; y

XV. Las demás normas que apruebe la asamblea.

---

**Procedencia**

- Versión: DOF 22-06-2018 · LFT: reformas DOF 30-05-2018 a 22-06-2018 · commit [`2ed3ea7`](https://github.com/BEG-lag/leyes-mx/commit/2ed3ea76ea8f4392c157407ddd139a6c93fe591e)
- Decretos que recoge esa versión:
  - DOF 30-05-2018: DECRETO por el que se reforma el artículo 265 de la Ley Federal del Trabajo. ([PDF](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_ref28_30may18.pdf))
  - DOF 22-06-2018: DECRETO por el que se expide la Ley Federal de Declaración Especial de Ausencia para Personas Desaparecidas, y se reforman diversas disposiciones de la Ley … ([PDF](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_ref29_22jun18.pdf))
- El texto de este artículo no cambia desde la versión DOF 12-06-2015 ([`bfe0764`](https://github.com/BEG-lag/leyes-mx/commit/bfe0764257eada5582487c7f9865b7e9866bbb14)).
- Notas editoriales de la Cámara en el artículo citan: DOF 30-04-1970, 30-11-2012.
- En GitHub: [leyes/lft.md, líneas 3999-4055, commit 2ed3ea7](https://github.com/BEG-lag/leyes-mx/blob/2ed3ea76ea8f4392c157407ddd139a6c93fe591e/leyes/lft.md?plain=1#L3999-L4055)

**Advertencias**

- Entre el DOF 22-06-2018 y el 01-06-2019 se publicaron reformas sin versión propia en el archivo (DOF 01-05-2019: DECRETO por el que se reforman, adicionan y derogan diversas disposiciones de la Ley Federal del Trabajo, de …). Su texto aparece en la siguiente versión del archivo, DOF 02-07-2019; el texto mostrado NO las refleja.
- Esta versión agrupa 2 reformas publicadas entre el DOF 30-05-2018 y el 22-06-2018: no hay copia archivada intermedia, así que el commit lleva la fecha de la última.
- En la siguiente versión archivada (DOF 02-07-2019) este artículo sí cambia y su nota editorial cita la reforma del DOF 01-05-2019, publicada antes del 01-06-2019: el texto mostrado está desactualizado para esa fecha. Usa diff_article o la fecha 2019-07-02 para ver el cambio.

> La fecha de cada versión es la de su publicación en el DOF. La entrada en vigor la fijan los transitorios de cada decreto (herramienta `transitorios`).

_No oficial. Solo el DOF es fuente auténtica. No es asesoría legal. Textos: versiones consolidadas de la Cámara de Diputados vía [leyes-mx](https://github.com/BEG-lag/leyes-mx)._
````

## transitorios

`{"law": "LFT", "decree_date": "2019-05-01", "max_chars": 4000}` · 0.00 s · ok

````markdown
# LFT · transitorios del decreto DOF 01-05-2019

Según la versión DOF 14-05-2026 (commit [`e3dd089`](https://github.com/BEG-lag/leyes-mx/commit/e3dd089ac05b8d7cab4a7313ed2c5afd126bf61b)), aplicable al 17-11-2026.

## DECRETO por el que se reforman, adicionan y derogan diversas disposiciones de la Ley Federal del Trabajo, de la Ley Orgánica del Poder Judicial de la Federación, de la Ley Federal de la Defensoría Pública, de la Ley del Instituto del Fondo Nacional de la Vivienda para los Trabajadores y de la Ley …

*Publicado en el Diario Oficial de la Federación el 1 de mayo de 2019*

**ARTÍCULO PRIMERO.** SE REFORMAN el párrafo primero y cuarto del artículo 3o.; el inciso a) de la fracción I del artículo 4o.; las fracciones III y VI del artículo 5o.; el segundo párrafo del artículo 22; la fracción III y V del artículo 28; el párrafo segundo del artículo 33; la fracción VI del artículo 42; los párrafos tercero y quinto del artículo 47; los párrafos primero, tercero y quinto del artículo 48; la fracción II y IV del artículo 49; el párrafo primero del artículo 57; el párrafo primero del artículo 75; el artículo 114; el párrafo segundo de la fracción IV del artículo 121; la fracción VI del artículo 127; la fracción XXVI del artículo 132; la fracción IV del artículo 133; el artículo 146; el artículo 152; el artículo 153; los párrafos primero y segundo del artículo 153-K; el párrafo primero del artículo 153-Q; el artículo 153-L; el artículo 153-N; el artículo 153-X; el artículo 157; el párrafo segundo del artículo 158; la fracción II del artículo 163; el artículo 164; el párrafo primero del artículo 176; el párrafo primero del artículo 207; el artículo 210; el párrafo primero del artículo 211; el artículo 245; la fracción II del artículo 273; el párrafo segundo del artículo 277; el párrafo primero del artículo 278; la fracción II del artículo 283; la denominación del capítulo XIII “Trabajadores del hogar”; el artículo 331; el párrafo primero del artículo 332; el artículo 333; el artículo 334; el artículo 336; las fracciones I y III del artículo 337; la fracción I del artículo 338; el párrafo primero del artículo 340; el artículo 342; las fracciones I y II del artículo 343-E; el artículo 353-O; el párrafo segundo del artículo 353-R; el párrafo primero del artículo 357; el párrafo primero del artículo 358; el artículo 364; el artículo 364 Bis; los párrafos primero y segundo, y las fracciones II y III del artículo 365; los párrafos primero y segundo del artículo 365 Bis; actuales párrafos primero y segundo del artículo 366, el artículo 368; los párrafos primero y segundo del artículo 369; las fracciones IX, X y XIII del artículo 371; los párrafos primero, actuales segundo, tercero, cuarto y quinto del artículo 373; el párrafo primero del artículo 374; el párrafo segundo del artículo 376; la fracción II y el párrafo segundo del artículo 377; el primer párrafo del artículo 384; los párrafos primero y segundo del artículo 387; la fracción I y III del artículo 388; el artículo 389; el párrafo primero del artículo 390; el artículo 391 Bis; artículo 392; el artículo 395; el párrafo primero del artículo 399; el párrafo segundo del artículo 399 Bis; la fracción I del artículo 401; artículo 407; artículo 408; artículo 409; el primer párrafo del artículo 411; la fracción III del artículo 412; artículo 414; las fracciones I, III, IV, V y VI inciso b) del artículo 415; el artículo 418; las fracciones II y IV del artículo 419; el párrafo segundo del artículo 419 Bis; el párrafo primero del artículo 421; las fracciones II y IV del artículo 424; el artículo 424 Bis; el párrafo primero del artículo 426; las fracciones I, II, III, y IV del artículo 429; el artículo 430; el artículo 431; el párrafo primero del artículo 432; las fracciones I, II y III del artículo 435; el artículo 439; el párrafo primero del artículo 448; el artículo 449; las fracciones II y III del artículo 451; la fracción III del artículo 459; la fracción IV del artículo 469; el artículo 476; el párrafo segundo del artículo 483; el primer párrafo del artículo 490; el artículo 493; el primer párrafo y las fracciones I, II, III y IV del artículo 501; el artículo 503; el párrafo primero de la fracción V del artículo 504; el artículo 505; el párrafo segundo del artículo 512-B; el párrafo primero del artículo 512-C; el párrafo primero del artículo 513; el párrafo segundo del artículo 514; la fracción III y el párrafo segundo del artículo 519; la fracción I del artículo 521; las fracciones X y XI …

_(texto recortado a 4,000 caracteres; ver completo en GitHub)_

[leyes/lft.md, líneas 17085-17237](https://github.com/BEG-lag/leyes-mx/blob/e3dd089ac05b8d7cab4a7313ed2c5afd126bf61b/leyes/lft.md?plain=1#L17085-L17237)

**Advertencias**

- Esta versión agrupa 7 reformas publicadas entre el DOF 19-12-2024 y el 14-05-2026: no hay copia archivada intermedia, así que el commit lleva la fecha de la última.

_No oficial. Solo el DOF es fuente auténtica. No es asesoría legal. Textos: versiones consolidadas de la Cámara de Diputados vía [leyes-mx](https://github.com/BEG-lag/leyes-mx)._
````

## search

`{"query": "subcontrat \"servicios especializados\"", "limit": 5}` · 1.10 s · ok

````markdown
# Búsqueda: `subcontrat "servicios especializados"` · texto aplicable al 17-11-2026

4 coincidencia(s) en 2 ley(es) (LFT 2, CFF 2). Se revisaron 13,370 secciones de 36 ley(es).

1. **LFT · Artículo 14.** · versión DOF 14-05-2026 · [ver](https://github.com/BEG-lag/leyes-mx/blob/e3dd089ac05b8d7cab4a7313ed2c5afd126bf61b/leyes/lft.md?plain=1#L220-L226)
   La **subcontrat**ación de servicios especializados o de ejecución de obras especializadas deberá formalizarse mediante contrato por escrito en el que se señale el objeto de los servicios a proporcionar o las obras a ejecutar, así como el número aproximado de traba …

2. **CFF · Artículo 15-D.** · versión DOF 09-04-2026 · [ver](https://github.com/BEG-lag/leyes-mx/blob/92e85cca4ce0d48126f5ef07c9fec3e058a67521/leyes/cff.md?plain=1#L402-L414)
   … o acreditamiento, los pagos o contraprestaciones realizados por concepto de **subcontrat**ación de personal para desempeñar actividades relacionadas tanto con el objeto social como con la actividad económica preponderante del contratante. Tampoco se dará …

3. **LFT · Artículo 13.** · versión DOF 14-05-2026 · [ver](https://github.com/BEG-lag/leyes-mx/blob/e3dd089ac05b8d7cab4a7313ed2c5afd126bf61b/leyes/lft.md?plain=1#L212-L218)
   Se permite la **subcontrat**ación de servicios especializados o de ejecución de obras especializadas que no formen parte del objeto social ni de la actividad económica preponderante de la beneficiaria de estos, siempre que el contratista esté registrado en el padr …

4. **CFF · Artículo 108.** · versión DOF 09-04-2026 · [ver](https://github.com/BEG-lag/leyes-mx/blob/92e85cca4ce0d48126f5ef07c9fec3e058a67521/leyes/cff.md?plain=1#L5501-L5565)
   … pérdidas fiscales inexistentes. i) Utilizar esquemas simulados de prestación de **servicios especializados** o la ejecución de obras especializadas, descritas en el artículo 15-D, penúltimo párrafo, de este Código, o realizar la subcontratación de personal a …

Búsqueda sin acentos ni mayúsculas; cada palabra es un prefijo y todas deben aparecer en el mismo artículo. Usa get_article para el texto completo.

_No oficial. Solo el DOF es fuente auténtica. No es asesoría legal. Textos: versiones consolidadas de la Cámara de Diputados vía [leyes-mx](https://github.com/BEG-lag/leyes-mx)._
````

## reforms

`{"law": "LFT", "since": "2019-01-01", "limit": 10}` · 0.00 s · ok

````markdown
# LFT · reformas

**Ley Federal del Trabajo** · [página de reformas](https://www.diputados.gob.mx/LeyesBiblio/ref/lft.htm)

Publicación original: DOF 01-04-1970 ([PDF](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_orig_01abr70_ima.pdf))

Decretos de reforma listados por LeyesBiblio: 54; desde el DOF 01-01-2019: 25. Versiones de LFT en git: 14 (desde DOF 17-01-2006).

| # | DOF | Decreto | En git |
|---:|---|---|---|
| 54 | 14-05-2026 | [DECRETO por el que se reforman y adicionan diversas disposiciones de la Ley Federal del Trabajo y de la Ley Federal del Derecho de Autor, en materia de derechos de las …](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_ref54_14may26.pdf) | versión propia DOF 14-05-2026 ([`e3dd089`](https://github.com/BEG-lag/leyes-mx/commit/e3dd089ac05b8d7cab4a7313ed2c5afd126bf61b)) |
| 53 | 01-05-2026 | [DECRETO por el que se reforman los artículos 40, fracción I, de la Ley Orgánica de la Administración Pública Federal; 15, fracciones IV y VI, de la Ley de Comercio …](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_ref53_01may26.pdf) | agrupada en la versión DOF 14-05-2026 ([`e3dd089`](https://github.com/BEG-lag/leyes-mx/commit/e3dd089ac05b8d7cab4a7313ed2c5afd126bf61b)) |
| 52 | 01-05-2026 | [DECRETO por el que se reforman, adicionan y derogan diversas disposiciones de la Ley Federal del Trabajo, en materia de reducción de la jornada laboral.](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_ref52_01may26.pdf) | agrupada en la versión DOF 14-05-2026 ([`e3dd089`](https://github.com/BEG-lag/leyes-mx/commit/e3dd089ac05b8d7cab4a7313ed2c5afd126bf61b)) |
| 51 | 15-01-2026 | [DECRETO por el que se reforman, adicionan y derogan diversas disposiciones de la Ley General para la Igualdad entre Mujeres y Hombres; de la Ley General de Acceso de las …](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_ref51_15ene26.pdf) | agrupada en la versión DOF 14-05-2026 ([`e3dd089`](https://github.com/BEG-lag/leyes-mx/commit/e3dd089ac05b8d7cab4a7313ed2c5afd126bf61b)) |
| 50 | 21-02-2025 | [DECRETO por el que se reforman, adicionan y derogan diversas disposiciones de la Ley del Instituto del Fondo Nacional de la Vivienda para los Trabajadores y de la Ley …](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_ref50_21feb25.pdf) | agrupada en la versión DOF 14-05-2026 ([`e3dd089`](https://github.com/BEG-lag/leyes-mx/commit/e3dd089ac05b8d7cab4a7313ed2c5afd126bf61b)) |
| 49 | 24-12-2024 | [DECRETO por el que se adicionan diversas disposiciones de la Ley Federal del Trabajo, en materia de Plataformas Digitales.](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_ref49_24dic24.pdf) | agrupada en la versión DOF 14-05-2026 ([`e3dd089`](https://github.com/BEG-lag/leyes-mx/commit/e3dd089ac05b8d7cab4a7313ed2c5afd126bf61b)) |
| 48 | 19-12-2024 | [DECRETO por el que se reforman y adicionan diversas disposiciones de la Ley Federal del Trabajo.](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_ref48_19dic24.pdf) | agrupada en la versión DOF 14-05-2026 ([`e3dd089`](https://github.com/BEG-lag/leyes-mx/commit/e3dd089ac05b8d7cab4a7313ed2c5afd126bf61b)) |
| 47 | 16-12-2024 | [DECRETO por el que se reforman y adicionan diversas disposiciones de la Ley Federal del Trabajo y de la Ley Federal de los Trabajadores al Servicio del Estado, …](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_ref47_16dic24.pdf) | versión propia DOF 16-12-2024 ([`435fe5e`](https://github.com/BEG-lag/leyes-mx/commit/435fe5eb81e142ab7136f46788ea4cc71e8acbd7)) |
| 46 | 30-09-2024 | [DECRETO por el que se reforma la fracción VII del artículo 74 de la Ley Federal del Trabajo, para establecer el 1o. de octubre de cada seis años, día de descanso …](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_ref46_30sep24.pdf) | agrupada en la versión DOF 16-12-2024 ([`435fe5e`](https://github.com/BEG-lag/leyes-mx/commit/435fe5eb81e142ab7136f46788ea4cc71e8acbd7)) |
| 45 | 04-04-2024 | [DECRETO por el que se reforma la fracción III del artículo 994 de la Ley Federal del Trabajo.](https://www.diputados.gob.mx/LeyesBiblio/ref/lft/LFT_ref45_04abr24.pdf) | versión propia DOF 04-04-2024 ([`20f877f`](https://github.com/BEG-lag/leyes-mx/commit/20f877f7f384cb2d2b3cd6dbd554a07f70b79853)) |

Mostrando los 10 más recientes de 25; usa `since` o `limit`.

**Notas**

- «Agrupada» significa que no hay copia archivada justo después de ese decreto: su texto aparece en la siguiente versión, junto con otras reformas.

_No oficial. Solo el DOF es fuente auténtica. No es asesoría legal. Textos: versiones consolidadas de la Cámara de Diputados vía [leyes-mx](https://github.com/BEG-lag/leyes-mx)._
````

## get_article

`{"law": "LISR", "article": "9"}` · 0.00 s · ok

````markdown
# LISR · Artículo 9.

**Ley del Impuesto sobre la Renta** › TÍTULO II · DE LAS PERSONAS MORALES

Texto aplicable al 17-11-2026: versión DOF 01-04-2024 (commit [`2a63e82`](https://github.com/BEG-lag/leyes-mx/commit/2a63e82f38e3896139dd480410c0dfed99b13121)).

---

Las personas morales deberán calcular el impuesto sobre la renta, aplicando al resultado fiscal obtenido en el ejercicio la tasa del 30%.

El resultado fiscal del ejercicio se determinará como sigue:

I. Se obtendrá la utilidad fiscal disminuyendo de la totalidad de los ingresos acumulables obtenidos en el ejercicio, las deducciones autorizadas por este Título y la participación de los trabajadores en las utilidades de las empresas pagada en el ejercicio, en los términos del artículo 123 de la Constitución Política de los Estados Unidos Mexicanos.

II. A la utilidad fiscal del ejercicio se le disminuirán, en su caso, las pérdidas fiscales pendientes de aplicar de ejercicios anteriores.

El impuesto del ejercicio se pagará mediante declaración que presentarán ante las oficinas autorizadas, dentro de los tres meses siguientes a la fecha en la que termine el ejercicio fiscal.

Para determinar la renta gravable a que se refiere el inciso e) de la fracción IX del artículo 123, apartado A de la Constitución Política de los Estados Unidos Mexicanos, no se disminuirá la participación de los trabajadores en las utilidades de las empresas pagada en el ejercicio ni las pérdidas fiscales pendientes de aplicar de ejercicios anteriores.

Para la determinación de la renta gravable en materia de participación de los trabajadores en las utilidades de las empresas, los contribuyentes deberán disminuir de los ingresos acumulables las cantidades que no hubiesen sido deducibles en los términos de la fracción XXX del artículo 28 de esta Ley.

---

**Procedencia**

- Versión: DOF 01-04-2024 · LISR: actualización DOF 01-04-2024 · commit [`2a63e82`](https://github.com/BEG-lag/leyes-mx/commit/2a63e82f38e3896139dd480410c0dfed99b13121)
- Nota del commit: La Cámara de Diputados actualizó el texto consolidado sin un decreto listado en su página de reformas para esta fecha.
- El texto de este artículo no cambia desde la versión DOF 11-12-2013 (la más antigua del archivo) ([`ae58808`](https://github.com/BEG-lag/leyes-mx/commit/ae58808c3055ba2143696b6679a48a9b8f418591)).
- En GitHub: [leyes/lisr.md, líneas 314-328, commit 2a63e82](https://github.com/BEG-lag/leyes-mx/blob/2a63e82f38e3896139dd480410c0dfed99b13121/leyes/lisr.md?plain=1#L314-L328)

**Advertencias**

- Entre el DOF 01-04-2024 y el 17-11-2026 se publicaron reformas sin versión propia en el archivo (DOF 13-11-2026: DECRETO por el que se reforman, adicionan y derogan diversas disposiciones de la Ley del Impuesto sobre la …). Todavía no hay una versión del texto consolidado que las incluya; el texto mostrado NO las refleja.

> La fecha de cada versión es la de su publicación en el DOF. La entrada en vigor la fijan los transitorios de cada decreto (herramienta `transitorios`).

_No oficial. Solo el DOF es fuente auténtica. No es asesoría legal. Textos: versiones consolidadas de la Cámara de Diputados vía [leyes-mx](https://github.com/BEG-lag/leyes-mx)._
````

## get_article

`{"law": "CCom", "article": "291", "date": "2010-01-01"}` · 0.00 s · error

````markdown
CCom no tiene el artículo 291 en la versión del DOF 27-08-2009 (aplicable al 01-01-2010). El artículo 291 sí aparece en versiones del DOF 28-03-2018 al 18-02-2026. Ojo: esta versión archivada tiene irregularidades de numeración en la fuente (falta el número 291).
````
