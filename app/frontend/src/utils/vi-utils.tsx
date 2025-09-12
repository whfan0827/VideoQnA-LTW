import { DocumentsById, VideoDocument } from "../api";
import { getSeconds } from "./time";

const VI_BASE_URL = "https://www.videoindexer.ai/embed/player";
export const getViCitationSrc = (docId: string, docsById: DocumentsById) => {
    const doc = docsById[docId];
    if (!doc) {
        console.error(`❌ getViCitationSrc: No document found for docId: ${docId}`);
        return "";
    }
    
    // Check required fields
    if (!doc.account_id) {
        console.error(`❌ getViCitationSrc: Missing account_id for docId: ${docId}`, doc);
        return "";
    }
    if (!doc.video_id) {
        console.error(`❌ getViCitationSrc: Missing video_id for docId: ${docId}`, doc);
        return "";
    }
    if (!doc.location) {
        console.error(`❌ getViCitationSrc: Missing location for docId: ${docId}`, doc);
        return "";
    }
    if (!doc.start_time) {
        console.error(`❌ getViCitationSrc: Missing start_time for docId: ${docId}`, doc);
        return "";
    }
    
    const time = getSeconds(doc.start_time);
    const url = `${VI_BASE_URL}/${doc.account_id}/${doc.video_id}?locale=en&location=${doc.location}&t=${time}&captions=en-US&showCaptions=true&boundingBoxes=detectedObjects,people`;
    
    console.log(`✅ getViCitationSrc: Generated URL for ${docId}:`, url);
    return url;
};

export const getVideoTitle = (docId: string = "", docsById: DocumentsById, displayStartTime: boolean = true, displayEndTime: boolean = false): string => {
    const doc = docsById[docId];
    if (!doc) {
        console.error(`❌ getVideoTitle: No document found for docId: ${docId}`);
        return `Document ${docId} (not found)`;
    }
    
    // Debug logging
    console.log(`🔍 getVideoTitle for ${docId}:`, {
        video_name: doc.video_name,
        start_time: doc.start_time,
        end_time: doc.end_time,
        displayStartTime,
        displayEndTime,
        hasVideoName: !!doc.video_name,
        hasStartTime: !!doc.start_time
    });
    
    // Fallback for missing video_name
    const videoName = doc.video_name || `Video ${docId}`;
    
    if (!doc.start_time) {
        console.warn(`⚠️ getVideoTitle: Missing start_time for ${docId}, returning name only`);
        return videoName;
    }
    
    const startTime = getFormattedStartTime(doc);
    if (displayStartTime && displayEndTime && doc.end_time) {
        const endTime = getFormattedEndTime(doc);
        return `${videoName} (${startTime} - ${endTime})`;
    }
    if (displayStartTime) {
        return `${videoName} (${startTime})`;
    }
    return videoName;
};

export const getFormattedStartTime = (doc: any) => {
    if (!doc || !doc.start_time) {
        console.warn('⚠️ getFormattedStartTime: Missing start_time', doc);
        return "0:00:00";
    }
    return doc.start_time.split(".")[0];
};

export const getFormattedEndTime = (doc: any) => {
    if (!doc || !doc.end_time) {
        console.warn('⚠️ getFormattedEndTime: Missing end_time', doc);
        return "0:00:00";
    }
    return doc.end_time.split(".")[0];
};
