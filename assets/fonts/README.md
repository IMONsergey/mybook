# Шрифты рабочей концепции

PT Serif и IBM Plex Sans. Тексты OFL сохранены рядом. Шрифтовые файлы не включены в репозиторий.

Для tools/build_visuals_v4.py нужны PTSerif-Regular.ttf, PTSerif-Italic.ttf, PTSerif-Bold.ttf и IBMPlexSans-Variable.ttf. Переменный IBM Plex Sans использует оси wght и wdth; жирное начертание задается значениями 700 и 100. В Word и Figma применяются названия семейств PT Serif и IBM Plex Sans.

Источники полученных файлов: https://github.com/google/fonts/tree/main/ofl/ptserif и https://github.com/google/fonts/tree/main/ofl/ibmplexsans. Имя переменного файла при локальной подготовке приведено к IBMPlexSans-Variable.ttf. Контроль лицензий и встраивания для выбранного издателя выполняется перед выпуском.

Для build_layout_v5.py нужны PTSerif-Regular.ttf, PTSerif-Italic.ttf и IBMPlexSans-Variable.ttf. Задать BOOK_FONTS как путь к папке с этими файлами или поместить их в assets/fonts/. Резервный путь среды сборки: /usr/local/share/fonts/book-v4/. Для правильного открытия Word установить семейства PT Serif и IBM Plex Sans в операционной системе; шрифты в DOCX не встроены.
