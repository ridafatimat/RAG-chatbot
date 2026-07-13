import { useId } from "react";

function normalizeCitations(citations) {
  if (!Array.isArray(citations)) return [];

  const unique = new Map();

  citations.forEach((citation) => {
    if (!citation || citation.source_number === undefined) return;

    const sourceNumber = Number(citation.source_number);
    if (!Number.isFinite(sourceNumber)) return;

    unique.set(sourceNumber, {
      ...citation,
      source_number: sourceNumber,
    });
  });

  return [...unique.values()].sort(
    (a, b) => a.source_number - b.source_number
  );
}

function CitationText({ value, citations, citationIdPrefix }) {
  if (value === null || value === undefined) return null;

  const text = String(value);
  const citationNumbers = new Set(
    citations.map((citation) => citation.source_number)
  );

  const parts = text.split(/(\[(?:\d+(?:\s*,\s*\d+)*)\])/g);

  const openCitation = (sourceNumber) => {
    const target = document.getElementById(
      `${citationIdPrefix}-source-${sourceNumber}`
    );

    if (!target) return;

    target.scrollIntoView({ behavior: "smooth", block: "center" });
    target.classList.add("citation-card-highlight");

    window.setTimeout(() => {
      target.classList.remove("citation-card-highlight");
    }, 1600);
  };

  return parts.map((part, partIndex) => {
    const markerMatch = part.match(/^\[([\d,\s]+)\]$/);

    if (!markerMatch) {
      return <span key={`text-${partIndex}`}>{part}</span>;
    }

    const numbers = markerMatch[1]
      .split(",")
      .map((number) => Number(number.trim()))
      .filter((number) => Number.isFinite(number));

    const availableNumbers = numbers.filter((number) =>
      citationNumbers.has(number)
    );

    if (availableNumbers.length === 0) {
      return <span key={`marker-${partIndex}`}>{part}</span>;
    }

    return (
      <span className="inline-citation-group" key={`marker-${partIndex}`}>
        {availableNumbers.map((sourceNumber) => (
          <button
            type="button"
            className="inline-citation"
            key={`${partIndex}-${sourceNumber}`}
            onClick={() => openCitation(sourceNumber)}
            title={`Open source ${sourceNumber}`}
            aria-label={`Open source ${sourceNumber}`}
          >
            [{sourceNumber}]
          </button>
        ))}
      </span>
    );
  });
}

function CitationList({ citations, citationIdPrefix, accentColor }) {
  if (citations.length === 0) return null;

  return (
    <section className="citation-section" aria-label="Answer sources">
      <div className="citation-section-heading">
        <span>Sources</span>
        <small>
          {citations.length} {citations.length === 1 ? "source" : "sources"}
        </small>
      </div>

      <div className="citation-list">
        {citations.map((citation) => (
          <article
            id={`${citationIdPrefix}-source-${citation.source_number}`}
            className="citation-card"
            key={citation.source_number}
            style={{ "--citation-accent": accentColor }}
          >
            <div className="citation-card-header">
              <span className="citation-number">
                [{citation.source_number}]
              </span>

              <div className="citation-card-title">
                <strong>
                  {citation.document_name || "Uploaded document"}
                </strong>
                <span>
                  {citation.source_label ||
                    `Chunk ${Number(citation.chunk_index ?? 0) + 1}`}
                </span>
              </div>
            </div>

            {citation.excerpt && (
              <p className="citation-excerpt">“{citation.excerpt}”</p>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

function StructuredAnswer({ message, accentColor = "#e53935" }) {
  const data = message?.structured_answer;
  const type = message?.answer_type;
  const citations = normalizeCitations(message?.citations);
  const reactId = useId().replace(/:/g, "");
  const citationIdPrefix = `answer-${reactId}`;

  const renderText = (value) => (
    <CitationText
      value={value}
      citations={citations}
      citationIdPrefix={citationIdPrefix}
    />
  );

  const cardStyle = {
    background: "#1f1f1f",
    border: "1px solid #2e2e2e",
    borderLeft: `4px solid ${accentColor}`,
    borderRadius: "12px",
    padding: "14px",
    marginBottom: "12px",
  };

  const optionStyle = {
    background: "#151515",
    border: "1px solid #2e2e2e",
    borderRadius: "8px",
    padding: "8px 10px",
    marginTop: "7px",
  };

  const renderTable = (block, index) => (
    <div key={index} style={{ overflowX: "auto", marginBottom: "12px" }}>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          background: "#1f1f1f",
          border: "1px solid #2e2e2e",
        }}
      >
        <thead>
          <tr>
            {(block.headers || []).map((header, i) => (
              <th
                key={i}
                style={{
                  border: "1px solid #2e2e2e",
                  padding: "10px",
                  color: accentColor,
                  textAlign: "left",
                }}
              >
                {renderText(header)}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {(block.rows || []).map((row, rowIndex) => (
            <tr key={rowIndex}>
              {(row || []).map((cell, cellIndex) => (
                <td
                  key={cellIndex}
                  style={{
                    border: "1px solid #2e2e2e",
                    padding: "10px",
                  }}
                >
                  {renderText(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const renderBlock = (block, index) => {
    const blockType = block.block_type || block.type;

    if (blockType === "heading") {
      return (
        <h3 key={index} style={{ color: accentColor, margin: "0 0 10px" }}>
          {renderText(block.content)}
        </h3>
      );
    }

    if (blockType === "paragraph") {
      return (
        <p key={index} style={{ margin: "0 0 12px", lineHeight: "1.6" }}>
          {renderText(block.content)}
        </p>
      );
    }

    if (blockType === "list") {
      return (
        <ul key={index} style={{ marginTop: 0, paddingLeft: "22px" }}>
          {(block.items || []).map((item, i) => (
            <li key={i} style={{ marginBottom: "6px" }}>
              {renderText(item)}
            </li>
          ))}
        </ul>
      );
    }

    if (blockType === "numbered_list") {
      return (
        <ol key={index} style={{ marginTop: 0, paddingLeft: "22px" }}>
          {(block.items || []).map((item, i) => (
            <li key={i} style={{ marginBottom: "6px" }}>
              {renderText(item)}
            </li>
          ))}
        </ol>
      );
    }

    if (blockType === "qa") {
      return (
        <div key={index} style={cardStyle}>
          <p style={{ margin: "0 0 8px", fontWeight: 700 }}>
            {renderText(block.question)}
          </p>

          {block.answer && (
            <p style={{ margin: 0 }}>
              <strong style={{ color: accentColor }}>Answer:</strong>{" "}
              {renderText(block.answer)}
            </p>
          )}
        </div>
      );
    }

    if (blockType === "mcq") {
      return (
        <div key={index} style={cardStyle}>
          <p style={{ margin: "0 0 10px", fontWeight: 700 }}>
            {renderText(block.question)}
          </p>

          {(block.options || []).map((option, i) => (
            <div key={i} style={optionStyle}>
              {renderText(option)}
            </div>
          ))}

          {block.answer && (
            <p style={{ margin: "12px 0 0", color: accentColor }}>
              <strong>Answer:</strong> {renderText(block.answer)}
            </p>
          )}
        </div>
      );
    }

    if (blockType === "table") {
      return renderTable(block, index);
    }

    if (blockType === "code") {
      return (
        <pre
          key={index}
          style={{
            background: "#101010",
            border: "1px solid #2e2e2e",
            borderRadius: "10px",
            padding: "12px",
            overflowX: "auto",
            marginBottom: "12px",
          }}
        >
          <code>{block.content}</code>
        </pre>
      );
    }

    if (blockType === "quote") {
      return (
        <blockquote
          key={index}
          style={{
            borderLeft: `4px solid ${accentColor}`,
            paddingLeft: "12px",
            margin: "0 0 12px",
            color: "#b5b5b5",
          }}
        >
          {renderText(block.content)}
        </blockquote>
      );
    }

    if (blockType === "warning") {
      return (
        <div
          key={index}
          style={{
            background: "#2a1f1f",
            border: `1px solid ${accentColor}`,
            borderRadius: "10px",
            padding: "12px",
            marginBottom: "12px",
          }}
        >
          <strong style={{ color: accentColor }}>Note:</strong>{" "}
          {renderText(block.content)}
        </div>
      );
    }

    return (
      <p key={index} style={{ marginBottom: "12px" }}>
        {renderText(block.content || JSON.stringify(block))}
      </p>
    );
  };

  const renderSources = () => (
    <CitationList
      citations={citations}
      citationIdPrefix={citationIdPrefix}
      accentColor={accentColor}
    />
  );

  if (!data || type === "plain") {
    return (
      <div className="structured-answer">
        <span>{renderText(message?.message)}</span>
        {renderSources()}
      </div>
    );
  }

  if (Array.isArray(data.blocks)) {
    return (
      <div className="structured-answer">
        {data.title && (
          <h3 style={{ color: accentColor, margin: "0 0 14px" }}>
            {renderText(data.title)}
          </h3>
        )}

        {data.blocks.map((block, index) => renderBlock(block, index))}
        {renderSources()}
      </div>
    );
  }

  // Backward compatibility for the old structured-answer formats.
  if (Array.isArray(data.questions)) {
    return (
      <div className="structured-answer">
        {data.title && (
          <h3 style={{ color: accentColor, margin: "0 0 14px" }}>
            {renderText(data.title)}
          </h3>
        )}

        {data.questions.map((question, index) =>
          renderBlock(
            question.options
              ? {
                  block_type: "mcq",
                  question: question.question,
                  options: question.options,
                  answer: question.answer,
                }
              : {
                  block_type: "qa",
                  question: question.question,
                  answer: question.answer,
                },
            index
          )
        )}

        {renderSources()}
      </div>
    );
  }

  if (Array.isArray(data.statements)) {
    return (
      <div className="structured-answer">
        {data.title && (
          <h3 style={{ color: accentColor, margin: "0 0 14px" }}>
            {renderText(data.title)}
          </h3>
        )}

        {data.statements.map((item, index) =>
          renderBlock(
            {
              block_type: "qa",
              question: item.statement,
              answer: item.answer,
            },
            index
          )
        )}

        {renderSources()}
      </div>
    );
  }

  return (
    <div className="structured-answer">
      <span>{renderText(message?.message)}</span>
      {renderSources()}
    </div>
  );
}

export default StructuredAnswer;