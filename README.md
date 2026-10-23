# Study Flash Cards

כרטיסיות לימוד לסטודנטים. בוחרים נושא, בוחרים מה מוצג בכרטיסייה ומה צריך לזהות (מבנה, שם, קיצור, קבוצה), ומתרגלים במצב **היפוך** או **אמריקאי**, עם ערבוב וחזרה על טעויות.

אתר סטטי (HTML, CSS ו-JavaScript בלי שלב בנייה), מתאים ל-Vercel ול-GitHub Pages.

## מבנה הפרויקט

```
index.html            דף הנחיתה ומסך הלימוד
assets/               עיצוב, קוד ואייקון
topics/index.json     רשימת הנושאים שמוצגת בדף הנחיתה
topics/<id>/topic.json  השדות, הקבוצות והכרטיסיות של נושא
topics/<id>/images/   תמונות הכרטיסיות (SVG)
tools/render_mol.py   ציור מבנים כימיים מ-SMILES עם RDKit
```

## הוספת נושא (אדמין)

העלאת נושאים עוברת דרך האדמין בלבד. התהליך:

1. שולחים את דף הלימוד (תמונה, PDF או Word) ל-Claude בפרויקט "Study Flash Cards".
2. Claude מזהה את הפריטים, מאמת את התוכן מול מקור חיצוני, מכין תמונות באיכות גבוהה ובודק אותן מול הדף.
3. הנושא נוסף כתיקייה חדשה תחת `topics/` ונרשם ב-`topics/index.json`.
4. דחיפה ל-GitHub מעדכנת את Vercel אוטומטית.

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
python -m http.server 8000
```
ואז לפתוח http://localhost:8000

## פריסה ל-Vercel

ב-Vercel: Add New → Project → Import לריפו הזה. בלי Build Command ובלי Output Directory (ברירת המחדל). מאותו רגע כל push ל-`main` מתפרסם.

## ציור מבנים כימיים

```
pip install -r tools/requirements.txt
python tools/render_mol.py
```
המבנים מצוירים מ-SMILES עם RDKit: אותו קנה מידה לכל המולקולות, ⁺H₃N משמאל, ⁻COO מימין, השרשרת הצדדית למעלה ומסומנת באפור. אטומים שמסומנים `:1` ב-SMILES מודגשים.
