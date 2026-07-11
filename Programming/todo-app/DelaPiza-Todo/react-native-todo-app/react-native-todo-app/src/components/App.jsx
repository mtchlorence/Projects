import { StatusBar } from 'expo-status-bar';
import { Text, View, SafeAreaView, TouchableOpacity } from 'react-native';
import { FlatList } from 'react-native';
import AddForm from './AddForm/AddFormContainer';
import { styles } from './AppStyles';
import Item from './Item/ItemContainer';
import { Ionicons } from '@expo/vector-icons';

const App = (props) => {
  const todoTasks = props.todos.filter((item) => item.state === 'todo');
  const completedTasks = props.todos.filter((item) => item.state === 'done');

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="auto" />
      <Text style={styles.headerTitle}>Mitch Lorence Dela Piza</Text>
      <View style={styles.separator} />
      <Text style={styles.pageTitle}>Inbox</Text>
      <View style={styles.separator} />

      <View style={styles.listView}>
        <Text style={styles.listTitle}>To Do</Text>
        {todoTasks.length !== 0 ? (
          <FlatList
            data={todoTasks}
            renderItem={({ item }) => <Item {...item} />}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.listContent}
          />
        ) : (
          <Text style={styles.emptyListText}>No to do tasks</Text>
        )}
      </View>
      <View style={styles.separator} />
      <View style={styles.listView}>
        <Text style={styles.listTitle}>Completed</Text>
        {completedTasks.length !== 0 ? (
          <FlatList
            data={completedTasks}
            renderItem={({ item }) => <Item {...item} />}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.listContent}
          />
        ) : (
          <Text style={styles.emptyListText}>No completed tasks</Text>
        )}
      </View>

      <TouchableOpacity style={styles.fab} onPress={() => {/* handle add task */}}>
        <Ionicons name="add" size={25} color="white" />
      </TouchableOpacity>

      <AddForm />
    </SafeAreaView>
  );
};

export default App;
