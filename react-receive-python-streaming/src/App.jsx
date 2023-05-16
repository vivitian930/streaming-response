import { Box, Button, Flex, Heading, Text, Textarea } from "@chakra-ui/react"

import { useEffect, useRef, useState } from "react"
import { SSE } from "sse"

import "./App.css"

function App() {
  let [prompt, setPrompt] = useState("")
  let [isLoading, setIsLoading] = useState(false)
  let [result, setResult] = useState("")

  const resultRef = useRef()

  useEffect(() => {
    resultRef.current = result
  }, [result])

  let handleClearBtnClicked = () => {
    setPrompt("")
    setResult("")
  }

  const handlePromptChange = (event) => {
    setPrompt(event.target.value)
  }
  // const API_KEY = "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"

  let handleSubmitPromptBtnClicked = async () => {
    if (prompt !== "") {
      setIsLoading(true)
      setResult("")
      let url = "http://localhost:8000/stream"
      let data = {
        message: prompt
      }

      let source = new SSE(url, {
        headers: {
          "Content-Type": "application/json"
        },
        method: "POST",
        payload: JSON.stringify(data)
      })

      source.addEventListener("message", (e) => {
        if (e.data != "[DONE]") {
          console.log(e.data, e.data.length)
          let payload = e.data.slice(1, -1)
          let text = payload
          // if (text == "\n") {
          //   text = "<br />"
          // }
          // console.log("Text: " + text)
          resultRef.current = resultRef.current + text
          // console.log("ResultRef.current: " + resultRef.current)
          setResult(resultRef.current)
        } else {
          source.close()
        }
      })

      source.addEventListener("readystatechange", (e) => {
        if (e.readyState >= 2) {
          setIsLoading(false)
        }
      })

      source.stream()
    } else {
      alert("Please insert a prompt!")
    }
  }
  return (
    <Flex
      width={"100vw"}
      height={"100vh"}
      alignContent={"center"}
      justifyContent={"center"}
      bgGradient="linear(to-b, orange.100, purple.300)"
    >
      <Box maxW="2xl" m="0 auto" p="20px">
        <Heading
          as="h1"
          textAlign="center"
          fontSize="5xl"
          mt="100px"
          bgGradient="linear(to-l, #7928CA, #FF0080)"
          bgClip="text"
        >
          React & OpenAI
        </Heading>
        <Heading as="h2" textAlign="center" fontSize="3xl" mt="20px">
          With Server Sent Events (SSE)
        </Heading>
        <Text fontSize="xl" textAlign="center" mt="30px">
          This is a React sample web application making use of OpenAI s GPT-3
          API to perform prompt completions. Results are received using Server
          Sent Events (SSE) in real-time.
        </Text>
        <Textarea
          value={prompt}
          onChange={handlePromptChange}
          placeholder="Insert your prompt here ..."
          mt="30px"
          size="lg"
        />
        <Button
          isLoading={isLoading}
          loadingText="Loading..."
          colorScheme="teal"
          size="lg"
          mt="30px"
          onClick={handleSubmitPromptBtnClicked}
        >
          Submit Prompt
        </Button>
        <Button
          colorScheme="teal"
          size="lg"
          mt="30px"
          ml="20px"
          onClick={handleClearBtnClicked}
        >
          Clear
        </Button>
        {result != "" && (
          <Box maxW="2xl" m="0 auto">
            <Heading as="h5" textAlign="left" fontSize="lg" mt="40px">
              Result:
            </Heading>
            <Text fontSize="lg" textAlign="left" mt="20px">
              {result}
            </Text>
          </Box>
        )}
      </Box>
    </Flex>
  )
}

export default App
