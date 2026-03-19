import React, { useEffect, useState } from "react";
import {
    Container, Select, Title, Text, Stack, Center, Button, Box,
    Modal, TextInput, Group, Notification,
} from "@mantine/core";
import { useNavigate } from 'react-router-dom'
import { get_brands, get_models, get_years, get_car_info } from "../Controllers/select_controller";
import { fetchVehicles, addManual } from "../Controllers/api_interactions";

export default function Home() {
    const [brand, setBrand] = useState(null)
    const [name, setName] = useState(null)
    const [year, setYear] = useState(null)
    const [brands, setBrands] = useState([])
    const [models, setModels] = useState([])
    const [years, setYears] = useState([])
    const [vehicleInfo, setVehicleInfo] = useState({})

    // Upload modal state
    const [uploadOpen, setUploadOpen] = useState(false)
    const [uploadLink, setUploadLink] = useState("")
    const [uploadMake, setUploadMake] = useState("")
    const [uploadModel, setUploadModel] = useState("")
    const [uploadYear, setUploadYear] = useState("")
    const [uploading, setUploading] = useState(false)
    const [uploadError, setUploadError] = useState(null)
    const [uploadSuccess, setUploadSuccess] = useState(false)

    const loadVehicles = async () => {
        try {
            const data = await fetchVehicles()
            setVehicleInfo(data)
            setBrands(get_brands(data))
        } catch (e) {
            console.error("Failed to load vehicles:", e)
        }
    }

    useEffect(() => {
        loadVehicles()
    }, [])

    const navigate = useNavigate()

    const handleUpload = async () => {
        if (!uploadLink.trim() || !uploadMake.trim() || !uploadModel.trim() || !uploadYear.trim()) return
        setUploading(true)
        setUploadError(null)
        setUploadSuccess(false)
        try {
            await addManual(uploadLink, uploadMake, uploadModel, uploadYear)
            setUploadSuccess(true)
            setUploadLink("")
            setUploadMake("")
            setUploadModel("")
            setUploadYear("")
            // Reset selections and reload vehicle list
            setBrand(null)
            setName(null)
            setYear(null)
            setModels([])
            setYears([])
            await loadVehicles()
        } catch (e) {
            setUploadError(e.message)
        } finally {
            setUploading(false)
        }
    }

    return (
        <Container pt="5rem" w="80%">
            <Stack ta="center">
                <Title c="black" size={"3rem"}>Welcome To <Text span c="blue" inherit>Car Manual AI</Text>!</Title>
                <Text fw={500} size="xl" pb="3rem" c="dimmed">Choose your vehicle's make and model to begin</Text>
                <Center>
                    <Select
                        clearable
                        pb="2rem"
                        onChange={(val) => {
                                setBrand(val)
                                setName(null)
                                setYears([])
                                if (val != null) {
                                    setModels(get_models(vehicleInfo, val))
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
                                    setYears(get_years(vehicleInfo, brand, val))
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
                    <Group gap="md">
                        <Button onClick={() => navigate("/chat", {state: {carInfo: get_car_info(vehicleInfo, brand, name, year)}})} disabled={brand === null || name === null || year == null} w="15rem" h="3rem" size="xl">Start Asking!</Button>
                        <Button variant="light" onClick={() => { setUploadOpen(true); setUploadSuccess(false); setUploadError(null); }} w="15rem" h="3rem" size="xl">Add Manual</Button>
                    </Group>
                </Center>
            </Stack>

            <Modal opened={uploadOpen} onClose={() => setUploadOpen(false)} title="Add Car Manual" size="md">
                <Stack>
                    <TextInput
                        label="PDF Link"
                        placeholder="https://example.com/manual.pdf"
                        value={uploadLink}
                        onChange={(e) => setUploadLink(e.target.value)}
                    />
                    <TextInput
                        label="Make"
                        placeholder="e.g. Honda"
                        value={uploadMake}
                        onChange={(e) => setUploadMake(e.target.value)}
                    />
                    <TextInput
                        label="Model"
                        placeholder="e.g. Civic"
                        value={uploadModel}
                        onChange={(e) => setUploadModel(e.target.value)}
                    />
                    <TextInput
                        label="Year"
                        placeholder="e.g. 2024"
                        value={uploadYear}
                        onChange={(e) => setUploadYear(e.target.value)}
                    />
                    {uploadError && (
                        <Notification color="red" onClose={() => setUploadError(null)}>
                            {uploadError}
                        </Notification>
                    )}
                    {uploadSuccess && (
                        <Notification color="green" onClose={() => setUploadSuccess(false)}>
                            Manual uploaded and processed successfully!
                        </Notification>
                    )}
                    <Button
                        onClick={handleUpload}
                        disabled={uploading || !uploadLink.trim() || !uploadMake.trim() || !uploadModel.trim() || !uploadYear.trim()}
                        loading={uploading}
                    >
                        {uploading ? "Processing..." : "Add Manual"}
                    </Button>
                    {uploading && (
                        <Text size="sm" c="dimmed" ta="center">
                            This may take a while as the PDF is being vectorized...
                        </Text>
                    )}
                </Stack>
            </Modal>
        </Container>
    );
}
