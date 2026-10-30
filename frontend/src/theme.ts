export const TEAM_COLORS: Record<string, string> = {
  McLaren: "#ff8700",
  Ferrari: "#e8002d",
  "Red Bull Racing": "#3671c6",
  Mercedes: "#27f4d2",
  "Aston Martin": "#229971",
  Williams: "#64c4ff",
  Audi: "#bb1424",
  Alpine: "#ff87bc",
  Haas: "#b6babd",
  "Racing Bulls": "#6692ff",
  Cadillac: "#d8d8dc",
};

export const colorFor = (team: string) => TEAM_COLORS[team] ?? "#e1222e";
