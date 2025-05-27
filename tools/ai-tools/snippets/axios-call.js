import axios from 'axios';

/**
 * makeApiCall(url: string, method: string = 'GET', data?: any)
 */
export async function makeApiCall(url, method = 'GET', data) {
  try {
    const response = await axios({ url, method, data });
    return response.data;
  } catch (error) {
    throw error;
  }
}
