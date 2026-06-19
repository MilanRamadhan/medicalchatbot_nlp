// The 30 diseases the fine-tuned RoBERTa model can classify.
// Source of truth: outputs/roberta_finetuned/label_mappings.json (labels_list).
// `en` = exact label emitted by the model (keep verbatim); `id` = Indonesian
// gloss shown as a tooltip for local users.

export interface Disease {
  en: string;
  id: string;
}

export const DISEASES: Disease[] = [
  { en: "Allergy", id: "Alergi" },
  { en: "Anemia", id: "Anemia" },
  { en: "Anxiety", id: "Gangguan kecemasan" },
  { en: "Arthritis", id: "Radang sendi" },
  { en: "Asthma", id: "Asma" },
  { en: "Bronchitis", id: "Bronkitis" },
  { en: "COVID-19", id: "COVID-19" },
  { en: "Chronic Kidney Disease", id: "Penyakit ginjal kronis" },
  { en: "Common Cold", id: "Selesma / pilek" },
  { en: "Dementia", id: "Demensia" },
  { en: "Depression", id: "Depresi" },
  { en: "Dermatitis", id: "Dermatitis (radang kulit)" },
  { en: "Diabetes", id: "Diabetes" },
  { en: "Epilepsy", id: "Epilepsi" },
  { en: "Food Poisoning", id: "Keracunan makanan" },
  { en: "Gastritis", id: "Gastritis (mag)" },
  { en: "Heart Disease", id: "Penyakit jantung" },
  { en: "Hypertension", id: "Hipertensi (darah tinggi)" },
  { en: "IBS", id: "Sindrom iritasi usus" },
  { en: "Influenza", id: "Influenza (flu)" },
  { en: "Liver Disease", id: "Penyakit hati / liver" },
  { en: "Migraine", id: "Migrain" },
  { en: "Obesity", id: "Obesitas" },
  { en: "Parkinson's", id: "Penyakit Parkinson" },
  { en: "Pneumonia", id: "Pneumonia (radang paru)" },
  { en: "Sinusitis", id: "Sinusitis" },
  { en: "Stroke", id: "Stroke" },
  { en: "Thyroid Disorder", id: "Gangguan tiroid" },
  { en: "Tuberculosis", id: "Tuberkulosis (TBC)" },
  { en: "Ulcer", id: "Tukak lambung" },
];
