function StructuredAnswer({ message, accentColor = "#e53935" }) {
  const data = message?.structured_answer;
  const type = message?.answer_type;

  if (!data || type === "plain") {
    return <span>{message?.message}</span>;
  }

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
                {header}
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
                  {cell}
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
          {block.content}
        </h3>
      );
    }

    if (blockType === "paragraph") {
      return (
        <p key={index} style={{ margin: "0 0 12px", lineHeight: "1.6" }}>
          {block.content}
        </p>
      );
    }

    if (blockType === "list") {
      return (
        <ul key={index} style={{ marginTop: 0, paddingLeft: "22px" }}>
          {(block.items || []).map((item, i) => (
            <li key={i} style={{ marginBottom: "6px" }}>
              {item}
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
              {item}
            </li>
          ))}
        </ol>
      );
    }

    if (blockType === "qa") {
      return (
        <div key={index} style={cardStyle}>
          <p style={{ margin: "0 0 8px", fontWeight: 700 }}>
            {block.question}
          </p>

          {block.answer && (
            <p style={{ margin: 0 }}>
              <strong style={{ color: accentColor }}>Answer:</strong>{" "}
              {block.answer}
            </p>
          )}
        </div>
      );
    }

    if (blockType === "mcq") {
      return (
        <div key={index} style={cardStyle}>
          <p style={{ margin: "0 0 10px", fontWeight: 700 }}>
            {block.question}
          </p>

          {(block.options || []).map((option, i) => (
            <div key={i} style={optionStyle}>
              {option}
            </div>
          ))}

          {block.answer && (
            <p style={{ margin: "12px 0 0", color: accentColor }}>
              <strong>Answer:</strong> {block.answer}
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
          {block.content}
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
          <strong style={{ color: accentColor }}>Note:</strong> {block.content}
        </div>
      );
    }

    return (
      <p key={index} style={{ marginBottom: "12px" }}>
        {block.content || JSON.stringify(block)}
      </p>
    );
  };

  if (Array.isArray(data.blocks)) {
    return (
      <div>
        {data.title && (
          <h3 style={{ color: accentColor, margin: "0 0 14px" }}>
            {data.title}
          </h3>
        )}

        {data.blocks.map((block, index) => renderBlock(block, index))}
      </div>
    );
  }

  // Backward compatibility for your old data format
  if (Array.isArray(data.questions)) {
    return (
      <div>
        {data.title && (
          <h3 style={{ color: accentColor, margin: "0 0 14px" }}>
            {data.title}
          </h3>
        )}

        {data.questions.map((q, index) =>
          renderBlock(
            q.options
              ? {
                  block_type: "mcq",
                  question: q.question,
                  options: q.options,
                  answer: q.answer,
                }
              : {
                  block_type: "qa",
                  question: q.question,
                  answer: q.answer,
                },
            index
          )
        )}
      </div>
    );
  }

  if (Array.isArray(data.statements)) {
    return (
      <div>
        {data.title && (
          <h3 style={{ color: accentColor, margin: "0 0 14px" }}>
            {data.title}
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
      </div>
    );
  }

  return <span>{message?.message}</span>;
}

export default StructuredAnswer;