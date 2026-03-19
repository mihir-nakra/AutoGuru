import React, { useState, useRef, useEffect } from "react";
import {
    Container,
    Paper,
    Textarea,
    Stack,
    Box,
    ScrollArea,
    ActionIcon,
    Text,
    Anchor,
    Loader,
    Group,
    Title,
} from "@mantine/core";

import { useLocation, useNavigate } from "react-router-dom";
import Markdown from "react-markdown";

import { perform_inference } from "../Controllers/api_interactions";

export default function Chat() {
    // Each message: { role: "user"|"assistant", text: string, sources: number[] }
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState("")
    const [isStreaming, setIsStreaming] = useState(false)
    const viewport = useRef(null)
    const navigate = useNavigate()

    const location = useLocation();
    const carInfo = location.state?.carInfo;

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        if (viewport.current) {
            viewport.current.scrollTo({ top: viewport.current.scrollHeight, behavior: "smooth" })
        }
    }, [messages])

    const handleSubmit = async () => {
        const question = input.trim()
        if (!question || isStreaming) return

        setInput("")
        setIsStreaming(true)

        // Add user message
        setMessages(prev => [...prev, { role: "user", text: question, sources: [] }])

        // Add empty assistant message that we'll stream into
        const assistantIndex = messages.length + 1
        setMessages(prev => [...prev, { role: "assistant", text: "", sources: [] }])

        let sources = []

        await perform_inference(
            question,
            carInfo.db_id,
            token => {
                setMessages(prev => {
                    const updated = [...prev]
                    updated[assistantIndex] = {
                        ...updated[assistantIndex],
                        text: updated[assistantIndex].text + token,
                    }
                    return updated
                })
            },
            source => {
                const pageNum = parseInt(source)
                if (!sources.includes(pageNum)) {
                    sources.push(pageNum)
                }
            }
        )

        // Finalize sources on the assistant message
        sources.sort((a, b) => a - b)
        setMessages(prev => {
            const updated = [...prev]
            updated[assistantIndex] = { ...updated[assistantIndex], sources }
            return updated
        })

        setIsStreaming(false)
    }

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            handleSubmit()
        }
    }

    return (
        <Box style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
            {/* Header */}
            <Group px="lg" py="sm" style={{ borderBottom: "1px solid var(--mantine-color-gray-3)" }}>
                <ActionIcon variant="subtle" size="lg" onClick={() => navigate("/")}>
                    <Text size="lg">&larr;</Text>
                </ActionIcon>
                <Title order={4}>
                    {carInfo ? `${carInfo.db_id.split("/").map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(" ")}` : "AutoGuru"}
                </Title>
            </Group>

            {/* Messages area */}
            <ScrollArea
                style={{ flex: 1 }}
                viewportRef={viewport}
                px="md"
            >
                <Container size="md" py="md">
                    {messages.length === 0 && (
                        <Text c="dimmed" ta="center" pt="xl" size="lg">
                            Ask a question about your vehicle!
                        </Text>
                    )}

                    {messages.map((msg, i) => (
                        <Box key={i} mb="md">
                            {msg.role === "user" ? (
                                <Group justify="flex-end">
                                    <Paper
                                        bg="blue.6"
                                        c="white"
                                        p="sm"
                                        px="md"
                                        radius="lg"
                                        maw="70%"
                                        style={{ borderBottomRightRadius: 4 }}
                                    >
                                        <Text size="sm">{msg.text}</Text>
                                    </Paper>
                                </Group>
                            ) : (
                                <Box maw="85%">
                                    <Paper
                                        bg="gray.0"
                                        p="sm"
                                        px="md"
                                        radius="lg"
                                        style={{ borderBottomLeftRadius: 4 }}
                                    >
                                        {msg.text === "" ? (
                                            <Loader size="sm" />
                                        ) : (
                                            <Box style={{ fontSize: "0.9rem" }}>
                                                <Markdown>{msg.text}</Markdown>
                                            </Box>
                                        )}
                                    </Paper>
                                    {msg.sources.length > 0 && (
                                        <Group gap="xs" mt={4} ml={4}>
                                            <Text size="xs" c="dimmed">Sources:</Text>
                                            {msg.sources.map(page => (
                                                <Anchor
                                                    key={page}
                                                    href={`${carInfo.link}#page=${page}`}
                                                    target="_blank"
                                                    size="xs"
                                                    c="blue.7"
                                                    underline="hover"
                                                >
                                                    Page {page}
                                                </Anchor>
                                            ))}
                                        </Group>
                                    )}
                                </Box>
                            )}
                        </Box>
                    ))}
                </Container>
            </ScrollArea>

            {/* Input area */}
            <Box px="md" py="sm" style={{ borderTop: "1px solid var(--mantine-color-gray-3)" }}>
                <Container size="md">
                    <Group align="flex-end" gap="sm">
                        <Textarea
                            style={{ flex: 1 }}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask about your vehicle..."
                            autosize
                            minRows={1}
                            maxRows={4}
                            disabled={isStreaming}
                        />
                        <ActionIcon
                            size="xl"
                            variant="filled"
                            onClick={handleSubmit}
                            disabled={isStreaming || !input.trim()}
                        >
                            <Text size="lg">&uarr;</Text>
                        </ActionIcon>
                    </Group>
                </Container>
            </Box>
        </Box>
    );
}
