// Converts a 3-letter or 2-letter country code to a flag emoji
const alpha3ToAlpha2 = {
  AUT: 'AT',
  GER: 'DE',
  IND: 'IN',
  SUI: 'CH',
  POL: 'PL',
  UKR: 'UA',
  LIE: 'LI',
  ITA: 'IT',
  BIH: 'BA',
  SVK: 'SK',
  ESP: 'ES',
  RUS: 'RU',
  PHI: 'PH',
  BUL: 'BG',
  LTU: 'LT',
  BEL: 'BE',
  CHN: 'CN',
  SYR: 'SY',
  KAZ: 'KZ',
  // ...add more as needed
};

export function countryCodeToFlag(code) {
  if (!code) return '';
  let cc = code.trim().toUpperCase();
  if (cc.length === 3) {
    if (alpha3ToAlpha2[cc]) {
      cc = alpha3ToAlpha2[cc];
    } else {
      return cc;
    }
  }
  if (cc.length !== 2) return '';
  return cc.replace(/./g, char =>
    String.fromCodePoint(127397 + char.charCodeAt())
  );
}
