import { renderToStaticMarkup } from "react-dom/server";
import { getViCitationSrc, getVideoTitle } from "../../utils/vi-utils";
import { AskResponse } from "../../api";

type HtmlParsedAnswer = {
    answerHtml: string;
    citations: string[];
    followupQuestions: string[];
};

export function parseAnswerToHtml(answer: AskResponse): HtmlParsedAnswer {
    const citations: string[] = [];
    const followupQuestions: string[] = [];

    // Extract any follow-up questions that might be in the answer
    let parsedAnswer = answer.answer.replace(/<<([^>>]+)>>/g, (match, content) => {
        followupQuestions.push(content);
        return "";
    });

    // trim any whitespace from the end of the answer after removing follow-up questions
    parsedAnswer = parsedAnswer.trim();

    const parts = parsedAnswer.split(/\[([^\]]+)\]/g);

    const fragments: string[] = parts.map((part, index) => {
        if (index % 2 === 0) {
            return part;
        } else {
            // Trim whitespace from citation ID to handle cases like "[ docId]"
            const trimmedPart = part.trim();
            
            // Extract UUID from citation format like "0826 大戰線 YT1 a464528b-a1a9-42a1-8697-d94976ab5fdd"
            // Look for UUID pattern at the end of the string
            const uuidMatch = trimmedPart.match(/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$/i);
            const docId = uuidMatch ? uuidMatch[1] : trimmedPart;
            
            let citationIndex: number;
            if (citations.indexOf(docId) !== -1) {
                citationIndex = citations.indexOf(docId) + 1;
            } else {
                citations.push(docId);
                citationIndex = citations.length;
            }

            const path = getViCitationSrc(docId, answer.docs_by_id);
            const title = getVideoTitle(docId, answer.docs_by_id);
            
            // Debug logging for citation parsing
            console.log(`🔍 Citation parsing: original="${part}", trimmed="${trimmedPart}", extracted_docId="${docId}", path="${path}", title="${title}"`);
            
            return renderToStaticMarkup(
                <a className="supContainer" title={title}>
                    <sup data-docid={docId} data-path={path}>
                        {citationIndex}
                    </sup>
                </a>
            );
        }
    });

    return {
        answerHtml: fragments.join(""),
        citations,
        followupQuestions
    };
}
