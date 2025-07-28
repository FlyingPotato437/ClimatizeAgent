import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

export const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE',
};

export function createSupabaseClient() {
  const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
  const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
  
  return createClient(supabaseUrl, supabaseServiceKey);
}

export function createApiResponse<T>(
  success: boolean, 
  data?: T, 
  error?: string,
  uploadUrls?: { permit?: string; bom?: string }
) {
  return new Response(
    JSON.stringify({
      success,
      data,
      error,
      uploadUrls
    }),
    {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: success ? 200 : 400,
    }
  );
}

export async function getSignedUploadUrl(
  supabase: any,
  bucket: string,
  filePath: string,
  expiresIn: number = 3600
): Promise<string | null> {
  try {
    const { data, error } = await supabase.storage
      .from(bucket)
      .createSignedUploadUrl(filePath, {
        expiresIn,
        upsert: true
      });

    if (error) {
      console.error('Error creating signed URL:', error);
      return null;
    }

    return data.signedUrl;
  } catch (error) {
    console.error('Error in getSignedUploadUrl:', error);
    return null;
  }
}

export async function downloadFileFromStorage(
  supabase: any,
  bucket: string,
  filePath: string
): Promise<Uint8Array | null> {
  try {
    const { data, error } = await supabase.storage
      .from(bucket)
      .download(filePath);

    if (error) {
      console.error('Error downloading file:', error);
      return null;
    }

    return new Uint8Array(await data.arrayBuffer());
  } catch (error) {
    console.error('Error in downloadFileFromStorage:', error);
    return null;
  }
}

export async function uploadFileToStorage(
  supabase: any,
  bucket: string,
  filePath: string,
  fileData: Uint8Array,
  contentType: string = 'application/octet-stream'
): Promise<string | null> {
  try {
    const { data, error } = await supabase.storage
      .from(bucket)
      .upload(filePath, fileData, {
        contentType,
        upsert: true
      });

    if (error) {
      console.error('Error uploading file:', error);
      return null;
    }

    // Get public URL
    const { data: urlData } = supabase.storage
      .from(bucket)
      .getPublicUrl(filePath);

    return urlData.publicUrl;
  } catch (error) {
    console.error('Error in uploadFileToStorage:', error);
    return null;
  }
}

export function parseCSVBOM(csvContent: string): any[] {
  const lines = csvContent.split('\n');
  
  // Find the data start
  let dataStart = 0;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('Row,Part Number')) {
      dataStart = i;
      break;
    }
  }

  if (dataStart === 0) return [];

  const dataLines = lines.slice(dataStart);
  const headers = dataLines[0].split(',').map(h => h.trim());
  const components = [];

  for (let i = 1; i < dataLines.length; i++) {
    const line = dataLines[i].trim();
    if (!line) continue;

    const values = line.split(',').map(v => v.trim());
    const component: any = {};

    headers.forEach((header, index) => {
      component[header.toLowerCase().replace(/\s+/g, '_')] = values[index] || '';
    });

    // Skip empty rows or total rows
    if (!component.part_number && !component.part_name) continue;
    if (component.row && component.row.toLowerCase().includes('total')) continue;

    // Ensure we have a display name
    component.part_name = component.part_name || component.part_number;
    
    components.push({
      row: components.length + 1,
      part_name: component.part_name,
      part_number: component.part_number,
      manufacturer: component.manufacturer || '',
      qty: component.qty || '1',
      category: component.category || ''
    });
  }

  return components;
}
