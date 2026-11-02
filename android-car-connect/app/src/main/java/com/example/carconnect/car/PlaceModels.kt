package com.example.carconnect.car

import androidx.car.app.model.CarLocation

data class DemoPlace(
    val id: String,
    val title: String,
    val address: String,
    val distanceKm: Double,
    val phone: String,
    val location: CarLocation
)

object DemoPlaces {
    val all: List<DemoPlace> = listOf(
        DemoPlace(
            id = "fuel",
            title = "Harbor Fuel",
            address = "120 Coastal Hwy",
            distanceKm = 1.2,
            phone = "+1-555-0101",
            location = CarLocation.create(37.7749, -122.4194)
        ),
        DemoPlace(
            id = "coffee",
            title = "Mile Marker Coffee",
            address = "88 Ridge Ave",
            distanceKm = 2.4,
            phone = "+1-555-0102",
            location = CarLocation.create(37.7849, -122.4094)
        ),
        DemoPlace(
            id = "parking",
            title = "Downtown Parking",
            address = "14 Market St",
            distanceKm = 3.1,
            phone = "+1-555-0103",
            location = CarLocation.create(37.7649, -122.4294)
        ),
        DemoPlace(
            id = "charging",
            title = "Green Charge Hub",
            address = "5 Electric Way",
            distanceKm = 4.6,
            phone = "+1-555-0104",
            location = CarLocation.create(37.7549, -122.4394)
        )
    )
}
