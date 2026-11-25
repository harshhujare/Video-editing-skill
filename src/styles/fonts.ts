import { continueRender, delayRender, staticFile } from 'remotion';

let loaded = false;

export const FONTS = {
  sans: '"Mukta", "Inter", "Noto Sans Devanagari", -apple-system, sans-serif',
  serifAccent: '"Rozha One", "Playfair Display Bold Italic", "Noto Serif Devanagari", Georgia, serif',
  devanagariSans: '"Mukta", "Noto Sans Devanagari", "Inter", sans-serif',
  devanagariSerif: '"Rozha One", "Noto Serif Devanagari", "Playfair Display Bold Italic", Georgia, serif',
  bodyMarathi: '"Mukta", "Noto Sans Devanagari", "Inter", sans-serif',
  displayKinetic: '"Mukta", "Inter", "Noto Sans Devanagari", sans-serif',
  displaySerif: '"Rozha One", "Playfair Display Bold Italic", "Noto Serif Devanagari", Georgia, serif',
  latinDisplayItalic: '"Playfair Display Bold Italic", "Inter", Georgia, serif',
  tabular: '"Inter", "Mukta", "Noto Sans Devanagari", sans-serif',
};

export const SWISS_PALETTE = {
  paper: '#F5F3EE',
  paperWarm: '#EDE9DF',
  darkGrid: '#0D0F12',
  darkSurface: '#141820',
  ink: '#141619',
  inkMuted: '#566070',
  cobalt: '#1E5EFF',
  cobaltDeep: '#09339E',
  emerald: '#16A34A',
  crimson: '#D62828',
  slate: '#4A5568',
  white: '#FFFFFF',
  borderLight: 'rgba(20, 22, 25, 0.16)',
  borderDark: 'rgba(245, 243, 238, 0.14)',
};

export const BRAND_COLORS = {
  neutralDark: '#0B1221',
  neutralLight: '#F3EFE6',
  accentBright: '#44A32C',
  inkMuted: '#566070',
  brandRed: '#D50B0A',
  brandRedBright: '#EF3B3A',
  brandNavy: '#09339E',
  brandRoyalBlue: '#0A35A4',
  brandGreen: '#44A32C',
  brandGreenDark: '#2C751B',
  brandGold: '#E3A009',
  brandGoldHighlight: '#FDDB38',
  brandBlack: '#020602',
  brandWhite: '#FEFEFE',
  surfacePaperWarm: '#F3EFE6',
  surfacePaperCool: '#E7E8E4',
  surfaceNewsprint: '#D7CFC2',
  surfaceDarkCard: '#131C31',
  inkOnLight: '#0E1420',
  inkOnDark: '#F7F5F0',
};

export const COLORS = {
  ...BRAND_COLORS,
  paperWhite: '#F3EFE6',
  paperPure: '#FFFFFF',
  charcoalCanvas: '#0B1221',
  accentCobalt: '#09339E',
  cobaltPaper: '#131C31',
  inkDark: '#0E1420',
  gridGlow: 'rgba(243, 239, 230, 0.10)',
};

export function splitMarathiAksharas(text: string): string[] {
  if (typeof Intl !== 'undefined' && 'Segmenter' in Intl) {
    const segmenter = new Intl.Segmenter('mr', { granularity: 'grapheme' });
    return Array.from(segmenter.segment(text), (s) => s.segment);
  }
  return Array.from(text);
}

export function ensureFontsLoaded(): void {
  if (loaded || typeof document === 'undefined' || !('FontFace' in window)) {
    return;
  }
  loaded = true;
  const specs = [
    { family: 'Inter', file: 'assets/fonts/Inter-Regular.ttf', weight: '400', style: 'normal' },
    { family: 'Inter', file: 'assets/fonts/Inter-Bold.ttf', weight: '700', style: 'normal' },
    {
      family: 'Playfair Display',
      file: 'assets/fonts/PlayfairDisplay-Italic.ttf',
      weight: '400',
      style: 'italic',
    },
    {
      family: 'Playfair Display',
      file: 'assets/fonts/PlayfairDisplay-BoldItalic.ttf',
      weight: '700',
      style: 'italic',
    },
    {
      family: 'Playfair Display Bold Italic',
      file: 'assets/fonts/PlayfairDisplay-BoldItalic.ttf',
      weight: '700',
      style: 'normal',
    },
    { family: 'Rozha One', file: 'assets/fonts/RozhaOne-Regular.ttf', weight: '400', style: 'normal' },
    { family: 'Rozha One', file: 'assets/fonts/RozhaOne-Regular.ttf', weight: '600', style: 'normal' },
    { family: 'Rozha One', file: 'assets/fonts/RozhaOne-Regular.ttf', weight: '700', style: 'normal' },
    { family: 'Khand', file: 'assets/fonts/Khand-SemiBold.ttf', weight: '600', style: 'normal' },
    { family: 'Khand', file: 'assets/fonts/Khand-Bold.ttf', weight: '700', style: 'normal' },
    { family: 'Khand', file: 'assets/fonts/Khand-Bold.ttf', weight: '800', style: 'normal' },
    { family: 'Khand', file: 'assets/fonts/Khand-Bold.ttf', weight: '900', style: 'normal' },
    { family: 'Mukta', file: 'assets/fonts/Mukta-SemiBold.ttf', weight: '400', style: 'normal' },
    { family: 'Mukta', file: 'assets/fonts/Mukta-SemiBold.ttf', weight: '600', style: 'normal' },
    { family: 'Mukta', file: 'assets/fonts/Mukta-ExtraBold.ttf', weight: '800', style: 'normal' },
    {
      family: 'Noto Sans Devanagari',
      file: 'assets/fonts/NotoSansDevanagari-Bold.ttf',
      weight: '700',
      style: 'normal',
    },
    {
      family: 'Noto Sans Devanagari',
      file: 'assets/fonts/NotoSansDevanagari-Bold.ttf',
      weight: '900',
      style: 'normal',
    },
    {
      family: 'Noto Serif Devanagari',
      file: 'assets/fonts/NotoSerifDevanagari-Bold.ttf',
      weight: '700',
      style: 'normal',
    },
  ];

  specs.forEach((spec) => {
    const handle = delayRender(`Loading font ${spec.family} ${spec.weight}`);
    const font = new FontFace(spec.family, `url('${staticFile(spec.file)}')`, {
      weight: spec.weight,
      style: spec.style,
    });
    font
      .load()
      .then((loadedFace) => {
        document.fonts.add(loadedFace);
        continueRender(handle);
      })
      .catch(() => {
        continueRender(handle);
      });
  });
}
