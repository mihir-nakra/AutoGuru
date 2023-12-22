import React, { useEffect, useState } from "react";
import { Container, Select, Title, Text, Stack, Center, Button, Box } from "@mantine/core";
import { useNavigate } from 'react-router-dom'
import { get_brands, get_models, get_years, get_car_info } from "../Controllers/select_controller";
import { init } from "../Controllers/api_interactions";

export default function Home() {
    const [brand, setBrand] = useState(null)
    const [name, setName] = useState(null)
    const [year, setYear] = useState(null)
    const [brands, setBrands] = useState([])
    const [models, setModels] = useState([])
    const [years, setYears] = useState([])

    useEffect(() => {
        init(true)
        setBrands(get_brands())
    }, [])

    const navigate = useNavigate()

    return (
        <Container pt="5rem" w="80%">
            <Stack ta="center">
                <Title c="black" size={"3rem"}>Welcome To <Text span c="blue" inherit>Car Manual AI</Text>!</Title>
                <Text fw={500} size="xl" pb="5rem" c="dimmed">Choose your vehicle's make and model to begin</Text>
                <Center>
                    <Select 
                        clearable
                        pb="2rem"
                        onChange={(val) => {
                                setBrand(val)
                                setYears([])
                                console.log(models)
                                console.log(val)
                                if (val != null) {
                                    setModels(get_models(val))
                                } else {
                                    setModels([])
                                }
                            }
                        }
                        w="100%"
                        label="Car Brand"
                        placeholder="Pick brand"
                        data={brands}
                    />
                </Center>
                <Center>
                    { models.length !== 0 ? <Select 
                        clearable
                        pb="2rem"
                        w="100%"
                        onChange={(val) => {
                                setName(val)
                                setYears([])
                                if (val != null) {
                                    setYears(get_years(brand, val))
                                } else {
                                    setYears([])
                                }
                            }
                        }
                        label="Car Model"
                        placeholder="Pick model"
                        data={models}
                    /> : <Box></Box>}
                </Center>
                <Center>
                    { years.length !== 0 ? <Select 
                        clearable
                        pb="3rem"
                        w="100%"
                        onChange={(val) => setYear(val)}
                        label="Car Year"
                        placeholder="Pick Year"
                        data={years}
                    /> : <Box></Box>}
                </Center>
                <Center>
                    <Button onClick={() => navigate("/chat", {state: {carInfo: get_car_info(brand, name, year)}})} disabled={brand === null || name === null || year == null} w="50%" h="3rem" size="xl">Start Asking!</Button>
                </Center>
            </Stack>
        </Container>
    );
}
