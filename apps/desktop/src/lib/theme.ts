export type Theme = "light" | "dark" | "system";

export function readTheme(): Theme {
  try {
    const value = localStorage.getItem("theme");
    return value === "light" || value === "dark" ? value : "system";
  } catch { return "system"; }
}

export function isDark(theme: Theme, systemDark: boolean) {
  return theme === "dark" || (theme === "system" && systemDark);
}
