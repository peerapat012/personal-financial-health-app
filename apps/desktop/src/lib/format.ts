const number = new Intl.NumberFormat("en-TH", { maximumFractionDigits: 2 });
const thb = new Intl.NumberFormat("en-TH", { style: "currency", currency: "THB", currencyDisplay: "narrowSymbol", minimumFractionDigits: 2 });
const date = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "Asia/Bangkok" });

export function formatDate(value: string | Date) {
  const parsed = typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value)
    ? new Date(`${value}T00:00:00+07:00`)
    : new Date(value);
  return date.format(parsed);
}

export function formatThb(value: string | number) {
  return thb.format(Number(value));
}

export function formatUnit(value: string | number, unit: string) {
  return `${number.format(Number(value))} ${unit}`;
}

export function formatWeight(value: string | number, unit = "kg") {
  return formatUnit(value, unit);
}

export function formatDuration(minutes: number) {
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return [hours && `${hours} hr`, remainder && `${remainder} min`].filter(Boolean).join(" ") || "0 min";
}
