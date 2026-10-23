# Study Flash Cards

כרטיסיות לימוד לסטודנטים. בוחרים נושא, בוחרים מה מוצג בכרטיסייה ומה צריך לזהות (מבנה, שם, קיצור, קבוצה), ומתרגלים במצב **היפוך** או **אמריקאי**, עם ערבוב וחזרה על טעויות.

אתר סטטי (HTML, CSS ו-JavaScript בלי שלב בנייה), מתאים ל-Vercel ול-GitHub Pages.

## מבנה הפרויקט

```
public/                         כל מה שמתפרסם באתר
public/index.html               דף הנחיתה ומסך הלימוד
public/assets/                  עיצוב, קוד ואייקון
public/topics/index.json        רשימת הנושאים שמוצגת בדף הנחיתה
public/topics/<id>/topic.json   השדות, הקבוצות והכרטיסיות של נושא
public/topics/<id>/images/      תמונות הכרטיסיות (SVG)
tools/render_mol.py   ציור מבנים כימיים מ-SMILES עם RDKit
```

## הוספת נושא (אדמין)

העלאת נושאים ועדכונם עוברים דרך האדמין בלבד, בשיחה עם Claude בפרויקט "Study Flash Cards". התהליך מתועד ב-`.claude/skills/add-topic/SKILL.md`:

1. שולחים ל-Claude את דף הלימוד (תמונה, PDF או Word): נושא חדש, הוספה לנושא קיים או עריכה.
2. Claude מזהה את הפריטים ומאמת כל פריט מול מקורות ברשת.
3. תמונות: מבנים כימיים מצוירים מחדש עם RDKit; פריטים אחרים נחתכים ומנוקים מהדף. תמונות מהרשת רק על פי בקשה, עם רישיון וקרדיט.
4. Claude שולח דף בדיקה עם כל הכרטיסיות, הסטטוס והמקורות.
5. אחרי אישור: בדיקת תקינות, דחיפה ל-GitHub, ופרסום אוטומטי ב-Vercel.

### כלים

```
python tools/build_topic.py drafts/<id>.json [--merge]   בניית נושא מטיוטה
python tools/validate.py                                  בדיקת תקינות לפני פרסום
python tools/preview.py <id> [out.html]                   דף בדיקה עם כל הכרטיסיות
python tools/render_mol.py [<id>]                         ציור מחדש של מבנים כימיים
```

הטיוטות נשמרות ב-`drafts/`, ומקורות האימות של כל נושא ב-`public/topics/<id>/sources.json`.

### מבנה `topic.json`

```json
{
  "id": "amino-acids",
  "title": "חומצות אמינו",
  "imageLabel": "מבנה",
  "groupLabel": "קבוצה",
  "fields": [{ "key": "name", "label": "שם" }],
  "groups": ["Polar"],
  "cards": [{ "id": "serine", "values": { "name": "Serine" }, "group": "Polar", "image": "images/serine.svg" }]
}
```

## הרצה מקומית

```
python -m http.server 8000 --directory public
```
ואז לפתוח http://localhost:8000

## פריסה ל-Vercel

ב-Vercel: Add New → Project → Import לריפו הזה. Framework Preset: Other. ההגדרות נקבעות ב-`vercel.json` (תיקיית הפלט: `public`). מאותו רגע כל push ל-`main` מתפרסם.

## ציור מבנים כימיים

```
pip install -r tools/requirements-dev.txt
python tools/render_mol.py
```
המבנים מצוירים מ-SMILES עם RDKit: אותו קנה מידה לכל המולקולות, ⁺H₃N משמאל, ⁻COO מימין, השרשרת הצדדית למעלה ומסומנת באפור. אטומים שמסומנים `:1` ב-SMILES מודגשים.
