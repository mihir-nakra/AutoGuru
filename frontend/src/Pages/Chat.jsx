import React, { useEffect, useState } from "react";
import {
    Container,
    Paper,
    Title,
    Textarea,
    Stack,
    Box,
    ScrollArea,
    Button,
    Text,
    Anchor,
    Loader,
    Group
} from "@mantine/core";

import { useLocation } from "react-router-dom";

import { perform_inference, init } from "../Controllers/api_interactions";

export default function Chat() {
    const [answer, setAnswer] = useState("")
    const [input, setInput] = useState("")
    const [canAsk, setCanAsk] = useState(true)
    const [pageSources, setPageSources] = useState([])
    const [loading, setLoading] = useState(false)
    
    useEffect(() => {
        init(true)
    }, [])

    const location = useLocation();
  
    const handleClick = async () => {
        setLoading(true)
        setAnswer("")
        if (canAsk) {
            setCanAsk(false)
            let sources = []
            setPageSources([])
            await perform_inference(input, 
                    location.state.carInfo.db_id,
                    text => {
                        setLoading(false)
                        setAnswer(prev => prev + text)
                    }, 
                    source => {
                        if (!sources.includes(parseInt(source))) {
                            sources.push(parseInt(source))
                        }
                    })
            sources.sort()
            setPageSources(sources)
            setCanAsk(true)
        }
    }

    const getSourceLinks = () => {
        return pageSources.map(source => {
            return <Anchor href={`${location.state.carInfo.link}#page=${source}`} c="blue.7" underline="hover">Page {source}</Anchor>
        })
    }

    return (
        <Container pt="5rem" w="95%">
                    <Stack justify="center">
                        {/* <Title c="black.3" order={2}>
                            Answer
                        </Title> */}
                        <Box bg="blue.1">
                        <ScrollArea p="1rem" h="15rem">
                            {answer === "" ? !loading ? <Text c="dimmed">Ask a question to get an answer!</Text> : <Loader /> : answer}
                        </ScrollArea>
                        <Group> 
                         <Text pl="10">Sources: </Text>
                            {getSourceLinks()}
                        </Group>
                      
                        </Box>
                        
                        <Textarea onChange={(event) => setInput(event.target.value)} w="100%" size="md" placeholder="How do I ...?" />
                        <Button disabled={!canAsk} onClick={handleClick}>Ask</Button>
                    </Stack>
        </Container>
    );
}
