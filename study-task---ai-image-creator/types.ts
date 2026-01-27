
export enum AppMode {
  GENERATE = 'GENERATE',
  EDIT = 'EDIT'
}

export type AspectRatio = '1:1' | '4:3' | '3:4' | '16:9' | '9:16';

export interface GenerationHistoryItem {
  id: string;
  url: string;
  prompt: string;
  timestamp: number;
  mode: AppMode;
}

export interface ImageConfig {
  aspectRatio: AspectRatio;
}
