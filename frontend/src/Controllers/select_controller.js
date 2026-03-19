export const get_brands = (info) => {
    let brands = Object.keys(info)
    for (let i in brands) {
        brands[i] = capitalize(brands[i])
    }
    return brands
}

export const get_models = (info, brand) => {
    brand = brand.toLowerCase()
    let models = Object.keys(info[brand])
    for (let i in models) {
        models[i] = capitalize(models[i])
    }
    return models
}

export const get_years = (info, brand, model) => {
    brand = brand.toLowerCase()
    model = model.toLowerCase()
    let years = Object.keys(info[brand][model])
    return years
}

export const get_car_info = (info, brand, model, year) => {
    brand = brand.toLowerCase()
    model = model.toLowerCase()
    return info[brand][model][year]
}

const capitalize = str => {
    return str.charAt(0).toUpperCase() + str.slice(1)
}
