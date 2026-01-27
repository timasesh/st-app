
import { GoogleGenAI } from "@google/genai";
import { AspectRatio } from "./types";

const MODEL_NAME = 'gemini-2.5-flash-image';

export const generateImage = async (prompt: string, aspectRatio: AspectRatio): Promise<string> => {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });
  
  const response = await ai.models.generateContent({
    model: MODEL_NAME,
    contents: {
      parts: [{ text: prompt }]
    },
    config: {
      imageConfig: {
        aspectRatio: aspectRatio
      }
    }
  });

  if (!response.candidates?.[0]?.content?.parts) {
    throw new Error("No response from AI");
  }

  for (const part of response.candidates[0].content.parts) {
    if (part.inlineData) {
      return `data:${part.inlineData.mimeType};base64,${part.inlineData.data}`;
    }
  }

  throw new Error("No image data found in response");
};

export const editImage = async (
  base64Data: string, 
  mimeType: string, 
  prompt: string, 
  aspectRatio: AspectRatio
): Promise<string> => {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });

  // Remove data:image/png;base64, prefix if present
  const cleanBase64 = base64Data.split(',')[1] || base64Data;

  const response = await ai.models.generateContent({
    model: MODEL_NAME,
    contents: {
      parts: [
        {
          inlineData: {
            data: cleanBase64,
            mimeType: mimeType
          }
        },
        { text: prompt }
      ]
    },
    config: {
      imageConfig: {
        aspectRatio: aspectRatio
      }
    }
  });

  if (!response.candidates?.[0]?.content?.parts) {
    throw new Error("No response from AI");
  }

  for (const part of response.candidates[0].content.parts) {
    if (part.inlineData) {
      return `data:${part.inlineData.mimeType};base64,${part.inlineData.data}`;
    }
  }

  throw new Error("No edited image data found in response");
};
