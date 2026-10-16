// AI-assisted: Generated with ChatGPT on [14/10/2026]. Modified by [Owusu Samuel].

// Importing the Material Design library for Flutter UI components
import 'package:flutter/material.dart';

// Entry point of the Flutter application
void main() {
  // Running the root widget of the application
  runApp(const MyApp());
}

// Root widget of the application, extending StatelessWidget
class MyApp extends StatelessWidget {
  // Constructor for MyApp with a key parameter for widget identification
  const MyApp({super.key});

  // Building the widget tree for the application
  @override
  Widget build(BuildContext context) {
    // Returning the MaterialApp widget which configures the app
    return MaterialApp(
      // Setting the application title
      title: 'INFT 425',
      // Defining the theme of the application
      theme: ThemeData(
        // Enabling Material Design 3 for modern UI styling
        useMaterial3: true,
        // Generating a color scheme from a purple seed color
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.purple),
      ),
      // Setting the home page widget of the application
      home: const HomePage(),
    );
  }
}

// Home page widget, extending StatelessWidget
class HomePage extends StatelessWidget {
  // Constructor for HomePage with a key parameter for widget identification
  const HomePage({super.key});

  // Building the widget tree for the home page
  @override
  Widget build(BuildContext context) {
    // Returning a Scaffold widget which provides the basic visual layout
    return Scaffold(
      // Defining the top app bar of the screen
      appBar: AppBar(
        // Setting the title text displayed on the app bar
        title: const Text('INFT 425 - Owusu Samuel '),
        // Setting the background color of the app bar to purple
        backgroundColor: Colors.purple,
      ),
      // Defining the main body content of the screen
      body: Center(
        // Arranging child widgets vertically in a column
        child: Column(
          // Centering the column's children vertically on the screen
          mainAxisAlignment: MainAxisAlignment.center,
          // Defining the list of child widgets inside the column
          children: const [
            // Displaying the "Hello World" greeting text
            Text(
              'Hello World',
              // Styling the greeting text with size, weight, and color
              style: TextStyle(
                fontSize: 36,
                fontWeight: FontWeight.bold,
                color: Colors.purple,
              ),
            ),
            // Adding vertical spacing between widgets
            SizedBox(height: 20),
            // Displaying a green code icon
            Icon(Icons.code, color: Colors.green, size: 50),
            // Adding vertical spacing between widgets
            SizedBox(height: 20),
            // Adding horizontal padding around the department text
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 20),
              // Displaying the department name text
              child: Text(
                'Department of Computing Sciences and Engineering',
                // Styling the department text with size and italic style
                style: TextStyle(fontSize: 16, fontStyle: FontStyle.italic),
                // Centering the department text horizontally
                textAlign: TextAlign.center,
              ),
            ),
            // Adding vertical spacing between widgets
            SizedBox(height: 20),
           
            // Displaying an orange school icon
            Icon(Icons.school, color: Colors.orange, size: 40),
          ],
        ),
      ),
    );
  }
}
