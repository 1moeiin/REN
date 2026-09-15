from django import forms

from .models import ContactMessage

INPUT = (
    "w-full border border-hairline bg-background px-4 py-3 text-ink "
    "placeholder:text-muted-foreground/60 focus:border-accent focus:outline-none "
    "focus:ring-2 focus:ring-accent/20 transition"
)


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "phone", "email", "subject", "message")
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT, "placeholder": "Adınız ve soyadınız"}),
            "phone": forms.TextInput(attrs={"class": INPUT, "placeholder": "0532 123 45 67"}),
            "email": forms.EmailInput(attrs={"class": INPUT, "placeholder": "eposta@ornek.com"}),
            "subject": forms.TextInput(attrs={"class": INPUT, "placeholder": "Mesaj konusu"}),
            "message": forms.Textarea(
                attrs={"class": INPUT, "rows": 5, "placeholder": "Mesajınız…"}
            ),
        }

    def clean_phone(self):
        # Accept Persian/Arabic-Indic digits too, store ASCII so the number stays
        # searchable however the visitor's keyboard happens to be set up.
        phone = self.cleaned_data["phone"]
        translated = phone.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
        digits = "".join(ch for ch in translated if ch.isdigit())
        if not 8 <= len(digits) <= 15:
            raise forms.ValidationError("Geçerli bir telefon numarası girin.")
        return digits
